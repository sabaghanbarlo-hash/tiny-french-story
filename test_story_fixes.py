import sys, tempfile, os, unittest
sys.path.insert(0, ".")
from PIL import Image
from tinyfr.parser import parse_script, Script, Say, SceneChange
from tinyfr import acting, scenes as SC, rig
from tinyfr.acting import NAMES, MIN_GAP
from tinyfr.config import CHAR_SCALE, BODY_W, W
from tinyfr.thumb import make_cover

L2 = open("lessons/02-journee-a-paris.txt", encoding="utf-8").read()
L3 = open("lessons/03-un-croissant.txt", encoding="utf-8").read()

def play(text):
    s = parse_script(text); return s, acting.play(s, lambda ev: 2.0)

class Spacing(unittest.TestCase):
    def test_idle_characters_keep_a_body_width_plus_air_between_them(self):
        for text in (L2, L3):
            _, (st, items, end) = play(text); t = 2.6; worst = 9999
            while t < end:
                p = {n: st.pose(n, t) for n in NAMES}
                if all(p[n]["vis"] and not p[n]["moving"] for n in NAMES):
                    worst = min(worst, abs(p["Marinette"]["x"] - p["Adrien"]["x"]))
                t += 0.04
            self.assertGreaterEqual(worst, MIN_GAP - 2)
    def test_drawn_bodies_never_touch_when_standing(self):
        body = BODY_W * CHAR_SCALE
        self.assertGreaterEqual(MIN_GAP - body, 90, "less than ~90px of air between two standing characters")
    def test_next_to_uses_the_wider_gap(self):
        st = acting.Stage("bakery"); x = st.resolve("Marinette", "next to adrien", 1)
        self.assertGreaterEqual(abs(x - st.cur["Adrien"]["x"]), MIN_GAP)

class Scale(unittest.TestCase):
    def test_sprite_is_scaled_to_the_scene(self):
        for k in SC.SCENES: self.assertTrue(0.3 <= SC.scale_of(k) <= 1.0)
    def test_walk_cycle_matches_ground_speed(self):
        _, (st, items, end) = play(L3)
        t = 2.6
        while t < end:
            P = st.pose("Marinette", t)
            if P["moving"]:
                self.assertAlmostEqual(P["phase"], P["x"] / (52.0 * SC.scale_of(st.scene)), places=6); return
            t += 0.04
        self.fail("nobody walked")

class AutoScene(unittest.TestCase):
    @staticmethod
    def script(title, fr="Bonjour !", en="Hello!", scene="auto", episode="1", story=None):
        return Script(dict(title=title, episode=episode, scene=scene), story if story is not None else [Say("Marinette", fr, en, "", 1)], [], [], [])
    def test_explicit_scene_still_works(self):
        self.assertEqual(SC.scene_for(self.script("x", scene="museum")), "museum")
        self.assertIsNone(SC.scene_for(self.script("x", scene="moon")))
    def test_auto_reads_the_story(self):
        self.assertEqual(SC.scene_for(self.script("Un croissant pour Adrien")), "bakery")
        self.assertEqual(SC.scene_for(self.script("x", fr="Je voudrais un livre.", en="I would like a book.")), "bookstore")
    def test_auto_follows_the_first_scene_change(self):
        s = self.script("x", story=[SceneChange("park", 5), Say("Marinette", "Salut !", "Hi!", "", 6)])
        self.assertEqual(SC.scene_for(s), "park")
    def test_auto_without_clues_varies_by_lesson(self):
        seen = {SC.scene_for(self.script(f"Lesson {i}", episode=str(i), fr="Ah.", en="Ah.")) for i in range(12)}
        self.assertGreaterEqual(len(seen), 4, seen)
        for name in seen: self.assertIn(name, SC.SCENES)
    def test_auto_script_plays(self):
        s = parse_script(L3.replace("scene: bakery", "scene: auto"))
        acting.check(s)

class Covers(unittest.TestCase):
    def test_story_cover(self):
        s = parse_script(L3)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "c.png"); make_cover(s, p); im = Image.open(p)
            self.assertEqual(im.size, (1080, 1920))
            self.assertNotEqual(im.tobytes(), SC.background("bakery").convert("RGB").tobytes())

if __name__ == "__main__": unittest.main(verbosity=1)
