import json, os, re, shutil, sys, tempfile, unittest
sys.path.insert(0, "."); sys.path.insert(0, "scripts")
import ci_render, studio

WF = open(".github/workflows/make-reel.yml", encoding="utf-8").read()
PAGE = open("docs/index.html", encoding="utf-8").read()
L4 = open("lessons/04-au-supermarche.txt", encoding="utf-8").read(); TAIL = L4[L4.index("[vocab]"):]
TINY = "title: Café test\nepisode: 9\nscene: bakery\n\n[story]\n@scene bakery\n> Camille enters left\nCamille: Bonjour ! | Hello!\n\n" + TAIL
BAD = "title: x\nscene: street\n\n[story]\n> Camille walks to nowhere\nCamille: Salut ! | Hi!\n\n" + TAIL

class Pages(unittest.TestCase):
    def test_samples_json_matches_lessons(self):
        self.assertEqual(json.load(open("docs/samples.json", encoding="utf-8")), studio.samples(), "run: python scripts/ci_render.py samples")
    def test_page_and_workflow_agree_on_inputs(self):
        wf = set(re.findall(r"(?m)^      (\w+):\s*$", WF.split("inputs:")[1].split("permissions:")[0]))
        page = set(re.findall(r"(\w+):", re.search(r"inputs:\{(.*?)\}\}\)\}\)", PAGE, re.S).group(1)))
        self.assertEqual(wf, {"script", "sections", "max_quiz", "test_mode"}); self.assertEqual(page, wf)
    def test_page_targets_this_repo_and_workflow(self):
        self.assertIn('REPO="sabaghanbarlo-hash/tiny-french-story"', PAGE); self.assertIn('WF="make-reel.yml"', PAGE); self.assertTrue(os.path.exists(".github/workflows/make-reel.yml"))
    def test_page_ids_exist(self):
        js = re.search(r"<script>(.*)</script>", PAGE, re.S).group(1)
        self.assertEqual(set(re.findall(r'\$\("(\w+)"\)', js)) - set(re.findall(r'id="(\w+)"', PAGE)), set())
    def test_page_uses_no_innerhtml_and_try_wrapped_storage(self):
        self.assertNotIn("innerHTML", PAGE); self.assertIn("try{localStorage", PAGE)
    def test_script_input_only_reaches_the_shell_through_env(self):
        hits = [l for l in WF.splitlines() if "inputs.script" in l]; self.assertEqual(len(hits), 1); self.assertTrue(hits[0].strip().startswith("SCRIPT:"))
    def test_workflow_never_posts_anywhere(self):
        text = (WF + open("scripts/ci_render.py", encoding="utf-8").read()).lower()
        for word in ("composio", "graph.facebook", "ig_account"): self.assertNotIn(word, text, word)

class Render(unittest.TestCase):
    def test_check_failure_reports_line_and_writes_result(self):
        with tempfile.TemporaryDirectory() as out:
            self.assertEqual(ci_render.render(out, {"SCRIPT": BAD}), 1); r = json.load(open(os.path.join(out, "result.json"), encoding="utf-8"))
            self.assertEqual((r["status"], r["stage"], r["line"]), ("error", "check", 5)); self.assertIn("nowhere", r["error"])
    def test_bad_options_are_rejected(self):
        with tempfile.TemporaryDirectory() as out:
            self.assertEqual(ci_render.render(out, {"SCRIPT": TINY, "SECTIONS": "nope", "MAX_QUIZ": "1"}), 1)
            self.assertEqual(ci_render.render(out, {"SCRIPT": TINY, "SECTIONS": "story", "MAX_QUIZ": "9"}), 1)
    def test_render_and_publish_end_to_end(self):
        with tempfile.TemporaryDirectory() as out, tempfile.TemporaryDirectory() as dest:
            self.assertEqual(ci_render.render(out, {"SCRIPT": TINY, "SECTIONS": "story", "MAX_QUIZ": "1", "TEST_MODE": "yes"}), 0)
            r = json.load(open(os.path.join(out, "result.json"), encoding="utf-8")); self.assertEqual((r["status"], r["title"], r["test_mode"]), ("done", "Café test", True))
            self.assertEqual(ci_render.publish(out, "123", dest=dest, use_git=False), 0)
            meta = json.load(open(os.path.join(dest, "reel-123.json"), encoding="utf-8")); self.assertEqual(set(meta["files"]), {"mp4", "srt", "caption.txt", "cover.png"})
            for f in meta["files"].values(): self.assertTrue(os.path.getsize(os.path.join(dest, f)) > 0, f)
            self.assertIn("Bonjour", open(os.path.join(dest, meta["files"]["srt"]), encoding="utf-8").read())
    def test_publish_prunes_to_newest_six_and_keeps_failures(self):
        with tempfile.TemporaryDirectory() as dest:
            for i in range(8):
                with tempfile.TemporaryDirectory() as out:
                    ci_render.write_result(out, status="error", stage="check", error="x"); ci_render.publish(out, str(1000 + i), dest=dest, use_git=False)
                    p = os.path.join(dest, f"reel-{1000 + i}.json"); m = json.load(open(p)); m["created_at"] = f"2026-10-23T10:00:{i:02d}Z"; json.dump(m, open(p, "w"))
            with tempfile.TemporaryDirectory() as out: ci_render.write_result(out, status="error", error="y"); ci_render.publish(out, "2000", dest=dest, use_git=False)
            names = sorted(f for f in os.listdir(dest) if f.endswith(".json")); self.assertEqual(len(names), 6); self.assertIn("reel-2000.json", names); self.assertNotIn("reel-1000.json", names)
    def test_publish_without_result_is_a_clean_failure(self):
        with tempfile.TemporaryDirectory() as out, tempfile.TemporaryDirectory() as dest: self.assertEqual(ci_render.publish(out, "1", dest=dest, use_git=False), 1)

if __name__ == "__main__": unittest.main(verbosity=1)
