import sys, unittest
sys.path.insert(0, ".")
from tinyfr.parser import parse_script
from tinyfr import acting, scenes, items, docsgen, meta
from tinyfr.config import W, H
L3 = open("lessons/03-un-croissant.txt", encoding="utf-8").read()

class Docs(unittest.TestCase):
    def test_docs_in_sync_with_code(self):
        self.assertEqual(open("DIRECTING.md", encoding="utf-8").read(), docsgen.directing())
        self.assertEqual(open("DIRECTOR_PROMPT.md", encoding="utf-8").read(), docsgen.prompt())
    def test_every_scene_spot_item_verb_listed(self):
        for f in ("DIRECTING.md", "DIRECTOR_PROMPT.md"):
            t = open(f, encoding="utf-8").read()
            for k, v in scenes.SCENES.items():
                self.assertIn("| " + k + " |", t)
                for sp in v["spots"]: self.assertIn(sp, t)
            for it in items.ITEMS: self.assertIn(it, t)
            for verb in acting.VERB_LIST: self.assertIn(verb, t)
    def test_example_in_docs_is_valid_and_reel_sized(self):
        s = parse_script(docsgen.example()); acting.check(s)
        from tinyfr.parser import Say
        n = sum(1 for e in s.story if isinstance(e, Say)); self.assertTrue(8 <= n <= 12, n)
    def test_prompt_mentions_unsupported_guard(self):
        self.assertIn("Do not invent other scenes", open("DIRECTOR_PROMPT.md", encoding="utf-8").read())

class Meta(unittest.TestCase):
    def test_caption(self):
        s = parse_script(L3); c = meta.caption(s)
        self.assertIn("délicieux — delicious", c); self.assertIn("Un croissant pour Julien", c)
        self.assertLessEqual(len(c), 2200); self.assertLessEqual(c.count("#"), 30)
    def test_cover(self):
        from tinyfr.thumb import make_cover
        from PIL import Image
        make_cover(parse_script(L3), "/tmp/cover_test.png"); self.assertEqual(Image.open("/tmp/cover_test.png").size, (W, H))
if __name__ == "__main__": unittest.main(verbosity=1)
