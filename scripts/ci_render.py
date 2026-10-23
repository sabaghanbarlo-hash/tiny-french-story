#!/usr/bin/env python3
"""Helper for the GitHub Pages studio (docs/index.html) and the 'Make Tiny French reel' workflow.

  python scripts/ci_render.py render OUT      validate $SCRIPT, render it, write OUT/result.json (exit 1 on failure)
  python scripts/ci_render.py publish OUT     copy results to docs/previews/reel-<RUN_ID>.* , prune old ones, commit + push
  python scripts/ci_render.py samples         regenerate docs/samples.json from lessons/*.txt

Nothing here posts to social media."""
import datetime, json, os, re, shutil, subprocess, sys, tempfile, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
import studio

KEEP = 6; EXTS = {".mp4": ".mp4", ".srt": ".srt", ".caption.txt": ".caption.txt", ".cover.png": ".cover.png"}
NET = re.compile(r"edge.?tts|ConnectionError|Cannot connect|Name or service|getaddrinfo|TimeoutError|NoAudioReceived", re.I)

def write_result(out, **r):
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "result.json"), "w", encoding="utf-8") as f: json.dump(r, f, ensure_ascii=False, indent=1)
    return r

def render(out, env=None):
    env = os.environ if env is None else env; t0 = time.time(); text = env.get("SCRIPT", "")
    v = studio.validate(text)
    if not v["ok"]:
        print(f"::error::Script problem: {v['error']}", file=sys.stderr); write_result(out, status="error", stage="check", error=v["error"], line=v.get("line")); return 1
    sections = [s for s in env.get("SECTIONS", "story,vocab,grammar,quiz").replace(" ", "").split(",") if s in studio.SECTIONS]
    try: mq = int(env.get("MAX_QUIZ", "1"))
    except ValueError: mq = 0
    if not sections or not 1 <= mq <= 3:
        write_result(out, status="error", stage="check", error="Pick at least one section and 1-3 quiz questions."); return 1
    dummy = env.get("TEST_MODE", "no").lower() in ("yes", "true", "1"); work = tempfile.mkdtemp(prefix="tf-ci-"); stem = studio.slug(v["title"] or "lesson")
    src = os.path.join(work, stem + ".txt")
    with open(src, "w", encoding="utf-8", newline="\n") as f: f.write(text)
    os.makedirs(out, exist_ok=True); cmd = [sys.executable, os.path.join(ROOT, "lesson.py"), src, "-o", out, "--sections", ",".join(sections), "--max-quiz", str(mq)] + (["--dummy-audio"] if dummy else [])
    try: p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=2400, env=dict(os.environ, PYTHONIOENCODING="utf-8", TF_LOWMEM="1")); code, log = p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired: code, log = -9, "Rendering took longer than 40 minutes and was stopped."
    finally: shutil.rmtree(work, ignore_errors=True)
    names = sorted(f for f in os.listdir(out) if any(f.endswith(e) for e in EXTS))
    if code == 0 and any(n.endswith(".mp4") for n in names):
        write_result(out, status="done", title=v["title"], episode=v["episode"], scenes=v["scenes"], seconds=round(time.time() - t0), test_mode=dummy, sections=sections); return 0
    last = (log.strip().splitlines() or ["The renderer stopped without a video."])[-1]
    print(f"::error::Render failed: {last}", file=sys.stderr); print(log[-2000:], file=sys.stderr)
    write_result(out, status="error", stage="render", error=last, hint=("French voices need internet (free edge-tts). Try again, or use test mode." if NET.search(log) else None)); return 1

def _git(*a, check=True): return subprocess.run(["git", *a], cwd=ROOT, check=check, capture_output=True, text=True)

def publish(out, run_id, dest=None, keep=KEEP, use_git=True):
    dest = dest or os.path.join(ROOT, "docs", "previews"); os.makedirs(dest, exist_ok=True)
    rp = os.path.join(out, "result.json")
    if not os.path.exists(rp): print("no result.json; nothing to publish"); return 1
    with open(rp, encoding="utf-8") as f: res = json.load(f)
    rid = f"reel-{run_id}"; res.update(id=str(run_id), created_at=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), files={})
    if res.get("status") == "done":
        for f in sorted(os.listdir(out)):
            for ext in EXTS:
                if f.endswith(ext): shutil.copy2(os.path.join(out, f), os.path.join(dest, rid + ext)); res["files"][ext.lstrip(".")] = rid + ext; break
    with open(os.path.join(dest, rid + ".json"), "w", encoding="utf-8") as f: json.dump(res, f, ensure_ascii=False, indent=1)
    items = []
    for f in os.listdir(dest):
        if f.endswith(".json"):
            try: items.append((json.load(open(os.path.join(dest, f), encoding="utf-8")).get("created_at", ""), f[:-5]))
            except (OSError, ValueError): pass
    for _, old in sorted(items, reverse=True)[keep:]:
        for f in os.listdir(dest):
            if f == old + ".json" or f.startswith(old + "."): os.remove(os.path.join(dest, f))
    if use_git:
        _git("add", "-A", "docs/previews"); _git("commit", "-m", f"preview: {rid} ({res.get('status')})", check=False)
        for i in range(5):
            if _git("push", check=False).returncode == 0: return 0
            _git("pull", "--rebase", "-X", "theirs", check=False); time.sleep(2 + i * 2)
        print("could not push the preview", file=sys.stderr); return 1
    return 0

def samples():
    s = studio.samples(); path = os.path.join(ROOT, "docs", "samples.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f: json.dump(s, f, ensure_ascii=False, indent=1); f.write("\n")
    print(f"wrote {len(s)} samples to docs/samples.json")

def main(argv):
    if len(argv) >= 3 and argv[1] == "render": return render(argv[2])
    if len(argv) >= 3 and argv[1] == "publish": return publish(argv[2], os.environ.get("RUN_ID", str(int(time.time()))))
    if len(argv) >= 2 and argv[1] == "samples": samples(); return 0
    print(__doc__); return 2

if __name__ == "__main__": sys.exit(main(sys.argv))
