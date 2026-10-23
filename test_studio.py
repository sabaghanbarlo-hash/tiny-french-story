import json, os, shutil, subprocess, sys, threading, time, unittest, urllib.error, urllib.request
sys.path.insert(0, ".")
import studio

L4 = open("lessons/04-au-supermarche.txt", encoding="utf-8").read()
TAIL = L4[L4.index("[vocab]"):]
TINY = "title: Café test\nepisode: 9\nscene: bakery\n\n[story]\n@scene bakery\n> Camille enters left\nCamille: Bonjour ! | Hello!\n\n" + TAIL
BAD = "title: x\nscene: street\n\n[story]\n> Camille walks to nowhere\nCamille: Salut ! | Hi!\n\n" + TAIL

class Studio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = studio.make_server(port=0); cls.port = cls.srv.server_address[1]; cls.base = f"http://127.0.0.1:{cls.port}"
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
    @classmethod
    def tearDownClass(cls): cls.srv.shutdown(); cls.srv.server_close(); shutil.rmtree(studio.WORK, ignore_errors=True)
    def call(self, path, body=None, headers=None, raw=None, method=None):
        h = dict(headers or {}); data = raw
        if body is not None: data = json.dumps(body).encode("utf-8"); h.setdefault("Content-Type", "application/json")
        req = urllib.request.Request(self.base + path, data=data, headers=h, method=method)
        try:
            with urllib.request.urlopen(req) as r: return r.status, r.read(), dict(r.headers)
        except urllib.error.HTTPError as e: return e.code, e.read(), dict(e.headers)
    def j(self, *a, **k): s, b, h = self.call(*a, **k); return s, json.loads(b.decode("utf-8"))

    def test_page_has_every_control(self):
        s, b, _ = self.call("/"); html = b.decode("utf-8"); self.assertEqual(s, 200)
        for i in ("script", "check", "make", "loadSample", "sample", "quiz", "dummy", "player", "files", "copy"): self.assertIn(f'id="{i}"', html)
        self.assertEqual(html.count('class="sec"'), 4)
    def test_samples_keep_accents(self):
        s, d = self.j("/api/samples"); self.assertEqual(s, 200); t = {x["name"]: x for x in d}
        self.assertIn("04-au-supermarche", t); self.assertIn("supermarché", t["04-au-supermarche"]["title"]); self.assertIn("Je veux", t["04-au-supermarche"]["script"])
    def test_validate_ok_utf8_roundtrip(self):
        s, v = self.j("/api/validate", {"script": TINY}); self.assertEqual(s, 200); self.assertTrue(v["ok"], v)
        self.assertEqual(v["title"], "Café test"); self.assertEqual(v["scenes"], ["bakery"]); self.assertEqual((v["vocab"], v["grammar"], v["quiz"]), (3, 1, 1))
    def test_validate_reports_line_number(self):
        s, v = self.j("/api/validate", {"script": BAD}); self.assertFalse(v["ok"]); self.assertEqual(v["line"], 5); self.assertIn("nowhere", v["error"])
    def test_validate_empty_and_too_long(self):
        self.assertFalse(self.j("/api/validate", {"script": "  "})[1]["ok"]); self.assertIn("too long", self.j("/api/validate", {"script": "a" * (studio.MAX_SCRIPT + 1)})[1]["error"])
    def test_validate_multiword_scene_in_summary(self):
        s = TINY.replace("@scene bakery", "@scene gare").replace("scene: bakery", "scene: train station")
        v = self.j("/api/validate", {"script": s})[1]; self.assertTrue(v["ok"], v); self.assertEqual(v["scenes"], ["train station"])
    def test_bad_requests(self):
        self.assertEqual(self.call("/api/validate", raw=b"{nope", headers={"Content-Type": "application/json"})[0], 400)
        self.assertEqual(self.call("/api/validate", raw=b"[]", headers={"Content-Type": "application/json"})[0], 400)
        self.assertEqual(self.call("/api/validate", raw=b"script=x", headers={"Content-Type": "application/x-www-form-urlencoded"})[0], 415)
        self.assertEqual(self.call("/api/validate", raw=b"x" * (studio.MAX_BODY + 1), headers={"Content-Type": "application/json"})[0], 413)
        self.assertEqual(self.call("/nope")[0], 404); self.assertEqual(self.call("/api/job/doesnotexist")[0], 404)
    def test_foreign_host_header_is_refused(self):
        self.assertEqual(self.call("/", headers={"Host": "evil.example.com"})[0], 403)
    def test_file_path_traversal_blocked(self):
        for p in ("/files/000000000000/../../studio.py", "/files/000000000000/..%2Fstudio.py", "/files/../studio.py"): self.assertEqual(self.call(p)[0], 404, p)
    def test_render_argument_validation(self):
        self.assertEqual(self.j("/api/render", {"script": BAD})[0], 422); self.assertEqual(self.j("/api/render", {"script": TINY, "sections": []})[0], 400)
        self.assertEqual(self.j("/api/render", {"script": TINY, "sections": ["story"], "max_quiz": 9})[0], 400); self.assertEqual(self.j("/api/render", {"script": TINY, "sections": ["hacks"]})[0], 400)
    def test_slug(self): self.assertEqual(studio.slug("Au supermarché avec Julien !"), "au-supermarche-avec-julien"); self.assertEqual(studio.slug("日本語"), "lesson")

    def test_zz_render_end_to_end(self):
        s, d = self.j("/api/render", {"script": TINY, "sections": ["story"], "max_quiz": 1, "dummy_audio": True}); self.assertEqual(s, 202, d); jid = d["id"]
        self.assertEqual(self.j("/api/render", {"script": TINY, "sections": ["story"], "dummy_audio": True})[0], 409, "second render must be refused while one runs")
        t0 = time.time()
        while time.time() - t0 < 240:
            _, st = self.j("/api/job/" + jid)
            if st["status"] != "running": break
            time.sleep(1)
        self.assertEqual(st["status"], "done", st); names = {f["name"] for f in st["files"]}
        self.assertTrue(any(n.endswith(".mp4") for n in names)); self.assertTrue(any(n.endswith(".srt") for n in names)); self.assertTrue(any(n.endswith(".caption.txt") for n in names)); self.assertTrue(any(n.endswith(".cover.png") for n in names))
        mp4 = next(f for f in st["files"] if f["name"].endswith(".mp4")); self.assertTrue(mp4["name"].startswith("cafe-test"))
        code, body, h = self.call(mp4["url"], headers={"Range": "bytes=0-99"}); self.assertEqual(code, 206); self.assertEqual(len(body), 100); self.assertTrue(h["Content-Range"].startswith("bytes 0-99/"))
        code, _, h = self.call(mp4["url"] + "?download=1"); self.assertIn("attachment", h["Content-Disposition"])
        srt = next(f for f in st["files"] if f["name"].endswith(".srt")); self.assertIn("Bonjour", self.call(srt["url"])[1].decode("utf-8"))
        if shutil.which("ffprobe"):
            out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", os.path.join(studio.JOBS[jid]["out"], mp4["name"])], capture_output=True, text=True).stdout.strip()
            self.assertEqual(out, "1080,1920")
        _, again = self.j("/api/render", {"script": BAD}); self.assertIn("error", again)

if __name__ == "__main__": unittest.main(verbosity=1)
