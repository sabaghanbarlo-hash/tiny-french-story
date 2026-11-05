#!/usr/bin/env python3
"""Pick the Reels from story-bank/ that are due to be rendered, a few days before they post.

Run by .github/workflows/daily-refill.yml. No AI, no API keys, no cost.

Every script in story-bank/ is named  YYYYMMDDHHMM-name.txt  (+ name.caption). The 12-digit prefix is the
time it posts, in UTC. A script is picked once its posting time is within DAYS_AHEAD days (default 4) and it
is not already waiting in the queue or posted. Each pick is checked with the real script checker first;
a broken one is renamed *.rejected so it can never stall the others.

Prints  plan=<stem>=<YYYY-MM-DDTHH:MMZ> ...  to $GITHUB_OUTPUT (stems to render, with their posting time).

  python refill_bank.py            do it
  python refill_bank.py --dry-run  show what would be picked, change nothing
  NOW=2026-11-06T05:30Z python refill_bank.py --dry-run     pretend it is another time (testing)
"""
import datetime as dt, glob, json, os, re, subprocess, sys

UTC = dt.timezone.utc
ROOT = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(ROOT, "story-bank")
AHEAD = int(os.environ.get("DAYS_AHEAD", "4") or 4)
DRY = "--dry-run" in sys.argv


def log(*a):
    print(*a, flush=True)


def now():
    n = os.environ.get("NOW", "").strip()
    if n:
        return dt.datetime.fromisoformat(n.replace("Z", "+00:00")).astimezone(UTC)
    return dt.datetime.now(UTC)


def stem(p):
    return os.path.splitext(os.path.basename(p))[0]


def known_stems():
    """Everything already in the queue (waiting, posted or failed)."""
    out = set()
    for folder in (os.path.join(ROOT, "queue"), os.path.join(ROOT, "queue", "done")):
        for p in glob.glob(os.path.join(folder, "*.json")):
            if os.path.basename(p) != "schedule.json":
                out.add(stem(p))
    return out


def post_time(name):
    m = re.match(r"^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})-", name)
    if not m:
        return None
    try:
        return dt.datetime(*map(int, m.groups()), tzinfo=UTC)
    except ValueError:
        return None


def valid(path):
    r = subprocess.run([sys.executable, os.path.join(ROOT, "small.py"), "--check", path], capture_output=True, text=True)
    if r.returncode != 0:
        log(f"::warning::{os.path.basename(path)} rejected by the script checker: {(r.stdout + r.stderr).strip()[-300:]}")
    return r.returncode == 0


def main():
    t = now()
    horizon = t + dt.timedelta(days=AHEAD)
    known = known_stems()
    scripts = sorted(glob.glob(os.path.join(BANK, "*.txt")))
    plan = []
    for txt in scripts:
        name = stem(txt)
        when = post_time(name)
        if when is None:
            log(f"::warning::{name}.txt has no YYYYMMDDHHMM- prefix, skipped.")
            continue
        if name in known:
            continue
        if when > horizon:
            continue
        if not os.path.exists(txt[:-4] + ".caption"):
            log(f"::warning::{name} has no .caption file, skipped.")
            continue
        if DRY:
            log(f"[dry-run] would render {name} for {when:%Y-%m-%d %H:%M} UTC")
            plan.append((name, when))
            continue
        if valid(txt):
            plan.append((name, when))
        else:
            os.rename(txt, txt[:-4] + ".rejected")
            os.rename(txt[:-4] + ".caption", txt[:-4] + ".caption.rejected")
    left = [s for s in scripts if stem(s) not in known and os.path.exists(s)]
    ahead_days = sorted({post_time(stem(s)) for s in left if post_time(stem(s))})
    log(f"Now {t:%Y-%m-%d %H:%M} UTC. Picked {len(plan)} (posting within {AHEAD} days). Scripts still in story-bank/: {len(left) - len(plan)} after this run.")
    remaining = len(left) - len(plan)
    if remaining <= 7:
        last = ahead_days[-1] if ahead_days else None
        log(f"::warning::Only {remaining} scripts left in story-bank/" + (f" (the last one posts {last:%b %d})" if last else "") + ". Time to add more.")
    out = os.environ.get("GITHUB_OUTPUT")
    if out and not DRY:
        with open(out, "a", encoding="utf-8") as f:
            f.write("plan=" + " ".join(f"{n}={w:%Y-%m-%dT%H:%MZ}" for n, w in plan) + "\n")


if __name__ == "__main__":
    main()
