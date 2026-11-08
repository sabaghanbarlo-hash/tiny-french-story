#!/usr/bin/env python3
"""Plan the Practice and Mistake & fix reels that are due to be rendered (bank-practice/ and bank-mistake/).

Same idea as refill_bank.py: every script is named YYYYMMDDHHMM-name.txt and the 12-digit prefix is the time it
posts (UTC). A script is picked once its posting time is within DAYS_AHEAD days (default 3) and it is not already in
the queue or posted. Each pick is checked with the real script checker; a broken one is renamed *.rejected.

Prints  plan=<style>:<stem>=<YYYY-MM-DDTHH:MMZ> ...  to $GITHUB_OUTPUT.   python refill_extra.py --dry-run  shows the plan only.
"""
import datetime as dt, glob, os, re, subprocess, sys

UTC = dt.timezone.utc
ROOT = os.path.dirname(os.path.abspath(__file__))
AHEAD = int(os.environ.get("DAYS_AHEAD", "3") or 3)
DRY = "--dry-run" in sys.argv
BANKS = {"practice": "bank-practice", "mistake": "bank-mistake"}


def log(*a):
    print(*a, flush=True)


def now():
    n = os.environ.get("NOW", "").strip()
    return dt.datetime.fromisoformat(n.replace("Z", "+00:00")).astimezone(UTC) if n else dt.datetime.now(UTC)


def stem(p):
    return os.path.splitext(os.path.basename(p))[0]


def known_stems():
    out = set()
    for folder in (os.path.join(ROOT, "queue"), os.path.join(ROOT, "queue", "done")):
        for p in glob.glob(os.path.join(folder, "*.json")):
            if os.path.basename(p) != "schedule.json":
                out.add(stem(p))
    return out


def post_time(name):
    m = re.match(r"^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})-", name)
    try:
        return dt.datetime(*map(int, m.groups()), tzinfo=UTC) if m else None
    except ValueError:
        return None


def valid(path):
    r = subprocess.run([sys.executable, os.path.join(ROOT, "small.py"), "--check", path], capture_output=True, text=True)
    if r.returncode != 0:
        log(f"::warning::{os.path.basename(path)} rejected by the script checker: {(r.stdout + r.stderr).strip()[-300:]}")
    return r.returncode == 0


def main():
    t = now(); horizon = t + dt.timedelta(days=AHEAD); known = known_stems(); plan = []
    for style, folder in BANKS.items():
        scripts = sorted(glob.glob(os.path.join(ROOT, folder, "*.txt")))
        for txt in scripts:
            name = stem(txt); when = post_time(name)
            if when is None:
                log(f"::warning::{folder}/{name}.txt has no YYYYMMDDHHMM- prefix, skipped."); continue
            if name in known or when > horizon:
                continue
            if DRY:
                log(f"[dry-run] would render {style}: {name} for {when:%Y-%m-%d %H:%M} UTC"); plan.append((style, name, when)); continue
            if valid(txt):
                plan.append((style, name, when))
            else:
                os.rename(txt, txt[:-4] + ".rejected")
        left = [s for s in scripts if os.path.exists(s) and stem(s) not in known and (style, stem(s)) not in [(p[0], p[1]) for p in plan]]
        log(f"{style}: {len(left)} scripts still waiting in {folder}/ after this run.")
        if len(left) <= 2:
            log(f"::warning::Only {len(left)} {style} scripts left in {folder}/. Time to add more.")
    out = os.environ.get("GITHUB_OUTPUT")
    if out and not DRY:
        with open(out, "a", encoding="utf-8") as f:
            f.write("plan=" + " ".join(f"{s}:{n}={w:%Y-%m-%dT%H:%MZ}" for s, n, w in plan) + "\n")


if __name__ == "__main__":
    main()
