#!/usr/bin/env python3
"""Posting queue for Tiny French Reels.

A finished video is added to the queue (queue/<stem>.json + queue/videos/<stem>.*) and gets the next free
"best time" slot. The scheduled workflow post-queue.yml posts whatever is due.

Commands: add | due | done | fail | show | reschedule | when
Slots and limits live in queue/schedule.json (UTC times).

You can also choose the exact time of any Reel instead of taking the next best slot:
    python queue_tool.py add --stem X --media-dir D --post-at 2026-10-30T18:30Z
    python queue_tool.py reschedule --stem X --post-at "2026-10-31 09:00"
Times without a zone are read as UTC; "+03:30" style offsets are understood too.
"""
import argparse, datetime as dt, glob, json, os, shutil, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(ROOT, "queue")
DEFAULTS = {"slots_utc": ["14:00", "01:00"], "max_per_day": 2, "min_gap_hours": 8, "lead_minutes": 30, "max_attempts": 3}
UTC = dt.timezone.utc


def utcnow():
    return dt.datetime.now(UTC)


def parse(ts):
    return dt.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def fmt(d):
    return d.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_when(text):
    """Read a time you typed: 2026-10-30T18:30Z, 2026-10-30 18:30, 2026-10-30T18:30:00+03:30. No zone means UTC. Returns UTC."""
    s = (text or "").strip()
    try:
        d = dt.datetime.fromisoformat(s.replace(" ", "T").replace("Z", "+00:00").replace("z", "+00:00"))
    except ValueError:
        raise ValueError(f"Can't read the time '{s}'. Use a form like 2026-10-30T18:30Z (UTC).") from None
    if len(s) <= 10:
        raise ValueError(f"Can't read the time '{s}': it needs a time as well as a date, like 2026-10-30T18:30Z (UTC).")
    return (d if d.tzinfo else d.replace(tzinfo=UTC)).astimezone(UTC).replace(microsecond=0)


def pick_time(now, taken, cfg, post_at=None):
    """The time a new Reel posts. Your own time wins (even over the daily cap); a time already gone means 'as soon as possible'."""
    if not post_at:
        return next_slot(now, taken, cfg), False
    want = parse_when(post_at)
    if want < now:
        print("Note: that time has already passed, so it will post at the next check (within about 15 minutes).")
        return now, True
    return want, True


def load_cfg():
    cfg = dict(DEFAULTS)
    p = os.path.join(QUEUE, "schedule.json")
    if os.path.exists(p):
        cfg.update({k: v for k, v in json.load(open(p, encoding="utf-8")).items() if k in DEFAULTS})
    return cfg


def next_slot(now, taken, cfg=None):
    """Earliest slot after now + lead time that respects the per-day cap and the minimum gap between posts."""
    cfg = cfg or DEFAULTS
    earliest = now + dt.timedelta(minutes=cfg["lead_minutes"])
    times = sorted(tuple(int(x) for x in s.split(":")) for s in cfg["slots_utc"])
    for offset in range(400):
        day = earliest.date() + dt.timedelta(days=offset)
        for h, m in times:
            c = dt.datetime(day.year, day.month, day.day, h, m, tzinfo=UTC)
            if c < earliest:
                continue
            if sum(1 for t in taken if t.date() == c.date()) >= cfg["max_per_day"]:
                continue
            if any(abs((c - t).total_seconds()) < cfg["min_gap_hours"] * 3600 for t in taken):
                continue
            return c
    raise RuntimeError("No free slot found")


def _read(folder):
    out = []
    for p in sorted(glob.glob(os.path.join(folder, "*.json"))):
        if os.path.basename(p) == "schedule.json":
            continue
        try:
            out.append((p, json.load(open(p, encoding="utf-8"))))
        except ValueError:
            pass
    return out


def _write(p, obj):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1); f.write("\n")


def cmd_add(a):
    cfg = load_cfg(); now = utcnow()
    src = a.media_dir
    meta = {}
    if os.path.exists(os.path.join(src, a.stem + ".json")):
        meta = json.load(open(os.path.join(src, a.stem + ".json"), encoding="utf-8"))
    taken = [parse(e["post_at"]) for _, e in _read(QUEUE) if e.get("status") == "pending"]
    taken += [parse(e["post_at"]) for _, e in _read(os.path.join(QUEUE, "done")) if parse(e["post_at"]) > now - dt.timedelta(days=3)]
    try:
        slot, mine = pick_time(now, taken, cfg, a.post_at)
    except ValueError as e:
        sys.exit(f"::error::{e}")
    vids = os.path.join(QUEUE, "videos"); os.makedirs(vids, exist_ok=True)
    for ext in ("mp4", "jpg", "srt", "caption.txt"):
        f = os.path.join(src, f"{a.stem}.{ext}")
        if os.path.exists(f):
            shutil.copy(f, os.path.join(vids, f"{a.stem}.{ext}"))
    if not os.path.exists(os.path.join(vids, a.stem + ".mp4")):
        sys.exit(f"No video found for {a.stem} in {src}")
    _write(os.path.join(QUEUE, a.stem + ".json"), {"stem": a.stem, "title": meta.get("title", a.stem), "format": a.format, "post_at": fmt(slot),
                                                   "queued_at": fmt(now), "status": "pending", "attempts": 0,
                                                   "scheduled_by": "you" if mine else "auto"})
    print(f"Queued {a.stem} for {fmt(slot)}" + (" (the time you chose)" if mine else ""))


def cmd_due(a):
    cfg = load_cfg(); now = utcnow()
    for _, e in sorted(_read(QUEUE), key=lambda x: x[1]["post_at"]):
        if e.get("status") == "pending" and parse(e["post_at"]) <= now and e.get("attempts", 0) < cfg["max_attempts"]:
            print(e["stem"])


def _drop_media(stem):
    for f in glob.glob(os.path.join(QUEUE, "videos", stem + ".*")):
        os.remove(f)


def cmd_done(a):
    p = os.path.join(QUEUE, a.stem + ".json"); e = json.load(open(p, encoding="utf-8"))
    e.update(status="posted", posted_at=fmt(utcnow()), media_id=a.media_id)
    os.makedirs(os.path.join(QUEUE, "done"), exist_ok=True)
    _write(os.path.join(QUEUE, "done", a.stem + ".json"), e); os.remove(p); _drop_media(a.stem)
    print(f"Marked {a.stem} as posted")


def cmd_fail(a):
    cfg = load_cfg(); p = os.path.join(QUEUE, a.stem + ".json"); e = json.load(open(p, encoding="utf-8"))
    e["attempts"] = e.get("attempts", 0) + 1
    if e["attempts"] >= cfg["max_attempts"]:
        e["status"] = "failed"
    _write(p, e); print(f"{a.stem}: attempt {e['attempts']} failed ({e['status']})")


def cmd_show(a):
    for _, e in _read(QUEUE):
        if not a.stem or e["stem"] == a.stem:
            print(f"- {e['title']} ({e['format']}): {e['status']}, post at {e['post_at']} UTC" + (" (time you chose)" if e.get("scheduled_by") == "you" else ""))


def cmd_reschedule(a):
    p = os.path.join(QUEUE, a.stem + ".json")
    if not os.path.exists(p):
        sys.exit(f"::error::{a.stem} is not waiting in the queue.")
    try:
        when = parse_when(a.post_at)
    except ValueError as e:
        sys.exit(f"::error::{e}")
    e = json.load(open(p, encoding="utf-8"))
    e.update(post_at=fmt(when), status="pending", attempts=0, scheduled_by="you")
    _write(p, e); print(f"{a.stem} will post at {fmt(when)}")


def cmd_when(a):
    try:
        print(fmt(parse_when(a.text)))
    except ValueError as e:
        sys.exit(f"::error::{e}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Tiny French posting queue")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add"); p.add_argument("--stem", required=True); p.add_argument("--media-dir", required=True); p.add_argument("--format", default="small"); p.add_argument("--post-at", default="", help="exact time to post, e.g. 2026-10-30T18:30Z (UTC); empty = next best slot"); p.set_defaults(fn=cmd_add)
    p = sub.add_parser("due"); p.set_defaults(fn=cmd_due)
    p = sub.add_parser("done"); p.add_argument("--stem", required=True); p.add_argument("--media-id", default=""); p.set_defaults(fn=cmd_done)
    p = sub.add_parser("fail"); p.add_argument("--stem", required=True); p.set_defaults(fn=cmd_fail)
    p = sub.add_parser("show"); p.add_argument("stem", nargs="?"); p.set_defaults(fn=cmd_show)
    p = sub.add_parser("reschedule"); p.add_argument("--stem", required=True); p.add_argument("--post-at", required=True); p.set_defaults(fn=cmd_reschedule)
    p = sub.add_parser("when"); p.add_argument("text"); p.set_defaults(fn=cmd_when)
    a = ap.parse_args(argv); a.fn(a)


if __name__ == "__main__":
    main()
