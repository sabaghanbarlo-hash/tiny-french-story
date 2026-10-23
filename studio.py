#!/usr/bin/env python3
"""Tiny French Studio - a local web page for writing, checking and rendering lessons.

    python studio.py            ->  http://127.0.0.1:8765

Standard library only. It runs the same `lesson.py` pipeline as the command line, one render at a time, on YOUR
computer. It cannot run on GitHub Pages (no Python/FFmpeg there). It listens on 127.0.0.1 only."""
import argparse, json, os, re, shutil, subprocess, sys, tempfile, threading, time, unicodedata, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote

ROOT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ROOT)
from tinyfr.parser import parse_script, ScriptError
from tinyfr import acting, scenes as SC

MAX_SCRIPT = 100_000; MAX_BODY = 200_000; SECTIONS = ("story", "vocab", "grammar", "quiz"); JOB_TIMEOUT = 1800; KEEP_JOBS = 5
JOBS, LOCK, WORK = {}, threading.Lock(), tempfile.mkdtemp(prefix="tinyfr-studio-")

def _read(path, binary=False):
    with open(path, "rb" if binary else "r", **({} if binary else {"encoding": "utf-8", "errors": "replace"})) as f: return f.read()

def slug(title):
    s = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode().lower(); s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:40] or "lesson"

def validate(text):
    """-> dict(ok, ...). Never raises for bad scripts; errors carry the parser's line number when it has one."""
    if not isinstance(text, str) or not text.strip(): return dict(ok=False, error="The script is empty.")
    if len(text) > MAX_SCRIPT: return dict(ok=False, error=f"The script is too long ({len(text)} characters; the limit is {MAX_SCRIPT}).")
    try:
        script = parse_script(text); acting.check(script)
    except ScriptError as e:
        m = re.search(r"line (\d+)", str(e)); return dict(ok=False, error=str(e), line=int(m.group(1)) if m else None)
    except Exception as e:   # a parser bug must not kill the server
        return dict(ok=False, error=f"Unexpected problem while checking the script: {type(e).__name__}: {e}")
    names = [SC.resolve(x) for x in re.findall(r"(?m)^@scene\s+(.+?)\s*$", text)] or [SC.resolve(script.meta.get("scene", "street"))]
    seen = []; [seen.append(n) for n in names if n not in seen]
    return dict(ok=True, title=script.meta.get("title"), episode=script.meta.get("episode"), scenes=seen, story_items=len(script.story), vocab=len(script.vocab), grammar=len(script.grammar), quiz=len(script.quiz))

def samples():
    out = []; d = os.path.join(ROOT, "lessons")
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f.endswith(".txt"):
            t = _read(os.path.join(d, f)); m = re.search(r"(?m)^title:\s*(.+)$", t)
            out.append(dict(name=f[:-4], title=m.group(1).strip() if m else f, script=t))
    return out

def _run(job, cmd):
    log = open(job["log"], "w", encoding="utf-8")
    try:
        p = subprocess.Popen(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, env=dict(os.environ, PYTHONIOENCODING="utf-8", TF_LOWMEM="1"))
        try: code = p.wait(timeout=JOB_TIMEOUT)
        except subprocess.TimeoutExpired: p.kill(); code = -9; job["error"] = f"Rendering took longer than {JOB_TIMEOUT // 60} minutes and was stopped."
    except Exception as e: code = -1; job["error"] = f"Could not start the renderer: {e}"
    finally: log.close()
    out = job["out"]; files = sorted((f for f in os.listdir(out) if os.path.isfile(os.path.join(out, f))), key=lambda f: (not f.endswith(".mp4"), f)) if os.path.isdir(out) else []
    job["files"] = [dict(name=f, size=os.path.getsize(os.path.join(out, f)), url=f"/files/{job['id']}/{f}") for f in files]
    has_mp4 = any(f["name"].endswith(".mp4") for f in job["files"])
    if code == 0 and has_mp4: job["status"] = "done"
    else:
        job["status"] = "error"; tail = job_log(job)
        job.setdefault("error", None); job["error"] = job["error"] or (tail.strip().splitlines() or ["The renderer stopped without a video."])[-1]
        if re.search(r"edge.?tts|ConnectionError|Cannot connect|Name or service|getaddrinfo|TimeoutError|NoAudioReceived", tail, re.I):
            job["hint"] = "French voices need an internet connection (free edge-tts). Reconnect and try again, or tick 'Test mode' to render with tones instead of voices (not for publishing)."
    job["finished"] = time.time()

def job_log(job, n=3000):
    try: return _read(job["log"])[-n:]
    except OSError: return ""

def start_render(text, sections, max_quiz, dummy):
    v = validate(text)
    if not v["ok"]: return 422, dict(error=v["error"], line=v.get("line"))
    sections = [s for s in sections if s in SECTIONS] if isinstance(sections, list) else []
    if not sections: return 400, dict(error="Pick at least one section to include.")
    if not isinstance(max_quiz, int) or not 1 <= max_quiz <= 3: return 400, dict(error="Quiz questions must be 1, 2 or 3.")
    with LOCK:
        if any(j["status"] == "running" for j in JOBS.values()): return 409, dict(error="A video is already being made. Wait for it to finish.")
        jid = uuid.uuid4().hex[:12]; d = os.path.join(WORK, jid); out = os.path.join(d, "out"); os.makedirs(out); stem = slug(v["title"] or "lesson")
        src = os.path.join(d, stem + ".txt"); _w = open(src, "w", encoding="utf-8", newline="\n"); _w.write(text); _w.close()
        job = dict(id=jid, status="running", started=time.time(), finished=None, log=os.path.join(d, "render.log"), out=out, dir=d, stem=stem, files=[], error=None, hint=None)
        JOBS[jid] = job
        for old in sorted(JOBS.values(), key=lambda j: j["started"])[:-KEEP_JOBS]:
            if old["status"] != "running": shutil.rmtree(old["dir"], ignore_errors=True); JOBS.pop(old["id"], None)
    cmd = [sys.executable, os.path.join(ROOT, "lesson.py"), src, "-o", out, "--sections", ",".join(sections), "--max-quiz", str(max_quiz)] + (["--dummy-audio"] if dummy else [])
    threading.Thread(target=_run, args=(job, cmd), daemon=True).start()
    return 202, dict(id=jid)

def job_view(job):
    end = job["finished"] or time.time()
    return dict(id=job["id"], status=job["status"], elapsed=round(end - job["started"], 1), files=job["files"], error=job["error"], hint=job["hint"], log=job_log(job, 1500))

class H(BaseHTTPRequestHandler):
    server_version = "TinyFrenchStudio"
    def log_message(self, *a): pass
    def _send(self, code, body, ctype="application/json; charset=utf-8", extra=None):
        if not isinstance(body, bytes): body = (json.dumps(body, ensure_ascii=False) if ctype.startswith("application/json") else body).encode("utf-8")
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(body))); self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items(): self.send_header(k, v)
        self.end_headers(); self.wfile.write(body)
    def _host_ok(self):   # blocks DNS-rebinding: only answer to localhost names
        h = (self.headers.get("Host") or "").split(":")[0].lower(); return h in ("127.0.0.1", "localhost", "[::1]") or self.server.allow_any_host
    def do_GET(self):
        if not self._host_ok(): return self._send(403, dict(error="Forbidden host"))
        u = urlparse(self.path); p = unquote(u.path)
        if p in ("/", "/index.html"): return self._send(200, _read(os.path.join(ROOT, "studio", "index.html"), True), "text/html; charset=utf-8")
        if p == "/api/samples": return self._send(200, samples())
        if p == "/api/directing":
            f = os.path.join(ROOT, "DIRECTING.md"); return self._send(200, dict(text=_read(f) if os.path.exists(f) else "DIRECTING.md not found."))
        if p.startswith("/api/job/"):
            j = JOBS.get(p.rsplit("/", 1)[1]); return self._send(200, job_view(j)) if j else self._send(404, dict(error="Unknown job"))
        m = re.fullmatch(r"/files/([0-9a-f]{12})/([^/\\]+)", p)
        if m:
            j = JOBS.get(m.group(1)); f = os.path.join(j["out"], m.group(2)) if j else None
            if not f or not os.path.isfile(f) or os.path.dirname(os.path.realpath(f)) != os.path.realpath(j["out"]): return self._send(404, dict(error="Not found"))
            return self._file(f, "download" in parse_qs(u.query))
        self._send(404, dict(error="Not found"))
    def _file(self, f, attach):
        size = os.path.getsize(f); ctype = {".mp4": "video/mp4", ".srt": "text/plain; charset=utf-8", ".txt": "text/plain; charset=utf-8", ".png": "image/png", ".json": "application/json"}.get(os.path.splitext(f)[1], "application/octet-stream")
        start, end, code = 0, size - 1, 200; r = re.fullmatch(r"bytes=(\d*)-(\d*)", self.headers.get("Range") or "")
        if r and (r.group(1) or r.group(2)):
            if r.group(1): start = int(r.group(1)); end = int(r.group(2)) if r.group(2) else size - 1
            else: start = max(0, size - int(r.group(2)))
            end = min(end, size - 1)
            if start > end: return self._send(416, b"", "text/plain", {"Content-Range": f"bytes */{size}"})
            code = 206
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Accept-Ranges", "bytes"); self.send_header("Content-Length", str(end - start + 1)); self.send_header("Cache-Control", "no-store")
        if code == 206: self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        if attach: self.send_header("Content-Disposition", f'attachment; filename="{os.path.basename(f)}"')
        self.end_headers()
        with open(f, "rb") as fh:
            fh.seek(start); left = end - start + 1
            while left > 0:
                chunk = fh.read(min(65536, left))
                if not chunk: break
                try: self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError): return
                left -= len(chunk)
    def do_POST(self):
        if not self._host_ok(): return self._send(403, dict(error="Forbidden host"))
        p = urlparse(self.path).path
        if p not in ("/api/validate", "/api/render"): return self._send(404, dict(error="Not found"))
        if "application/json" not in (self.headers.get("Content-Type") or ""): return self._send(415, dict(error="Send JSON."))
        try: n = int(self.headers.get("Content-Length") or 0)
        except ValueError: n = -1
        if n < 0 or n > MAX_BODY: return self._send(413, dict(error="Request too large."))
        try: data = json.loads(self.rfile.read(n).decode("utf-8")); assert isinstance(data, dict)
        except Exception: return self._send(400, dict(error="That request was not valid JSON."))
        if p == "/api/validate": return self._send(200, validate(data.get("script")))
        code, body = start_render(data.get("script"), data.get("sections", list(SECTIONS)), data.get("max_quiz", 1), bool(data.get("dummy_audio")))
        self._send(code, body)

def make_server(host="127.0.0.1", port=8765, allow_any_host=False):
    srv = ThreadingHTTPServer((host, port), H); srv.allow_any_host = allow_any_host; srv.daemon_threads = True; return srv

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0]); ap.add_argument("--port", type=int, default=8765); ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--host", default="127.0.0.1", help="address to listen on (default: this computer only)")
    ap.add_argument("--allow-any-host", action="store_true", help="accept any Host header; only for private forwarded ports such as GitHub Codespaces")
    a = ap.parse_args(); srv = make_server(a.host, a.port, a.allow_any_host); shown = "127.0.0.1" if a.host == "0.0.0.0" else a.host; url = f"http://{shown}:{srv.server_address[1]}"
    print(f"Tiny French Studio running at {url}   (Ctrl+C to stop)\nVideos are made on this computer; files are kept in {WORK} until you close the studio.")
    if not a.no_browser:
        import webbrowser; threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try: srv.serve_forever()
    except KeyboardInterrupt: print("\nStopped.")
    finally: shutil.rmtree(WORK, ignore_errors=True)

if __name__ == "__main__": main()
