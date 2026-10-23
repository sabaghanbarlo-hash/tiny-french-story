import sys, unittest
sys.path.insert(0, ".")
import numpy as np
from tinyfr import acting, scenes
from tinyfr.acting import MIN_GAP, W
from tinyfr.parser import parse_script
L1 = open("lessons/01-bakery.txt", encoding="utf-8").read()
TAIL = L1[L1.index("[vocab]"):]

def script_for(scene, spots):
    lines = ["title: Test " + scene, "episode: 1", "scene: " + scene, "", "[story]", "@scene " + scene, "> Camille enters left", "& Julien enters left", "Camille: Bonjour ! | Hello!"]
    for i, sp in enumerate(spots):
        who = "Camille" if i % 2 == 0 else "Julien"
        lines += [f"> {who} walks to {sp}", f"{who}: Salut ! | Hi!"]
    return "\n".join(lines) + "\n\n" + TAIL

class Scenes(unittest.TestCase):
    def test_every_scene_renders_vertical_and_not_blank(self):
        for k in scenes.SCENES:
            im = scenes.background(k); self.assertEqual(im.size, (1080, 1920), k)
            self.assertGreater(float(np.asarray(im.convert("L"), dtype=float).std()), 15, k + " looks blank")
    def test_spots_are_walkable_and_spaced(self):
        for k, v in scenes.SCENES.items():
            xs = sorted(v["spots"].values()); self.assertTrue(v["spots"], k)
            for x in xs: self.assertTrue(100 <= x <= W - 100, f"{k}: spot at x={x} too close to the edge")
            for a, b in zip(xs, xs[1:]): self.assertGreaterEqual(b - a, MIN_GAP, f"{k}: spots closer than MIN_GAP")
    def test_aliases_unique_and_resolve(self):
        seen = {}
        for k, v in scenes.SCENES.items():
            for a in [k] + v["aliases"]:
                self.assertNotIn(a, seen, f"{a!r} is claimed by both {seen.get(a)} and {k}"); seen[a] = k
                self.assertEqual(scenes.resolve(a.upper()), k)
    def test_scenes_look_different(self):
        small = {k: np.asarray(scenes.background(k).convert("L").resize((54, 96)), dtype=float) for k in scenes.SCENES}; ks = list(small)
        for i, a in enumerate(ks):
            for b in ks[i + 1:]: self.assertGreater(float(np.abs(small[a] - small[b]).mean()), 6, f"{a} and {b} are nearly identical")
    def test_every_scene_can_be_directed_to_every_spot(self):
        for k, v in scenes.SCENES.items():
            s = parse_script(script_for(k, list(v["spots"]))); acting.check(s)
            st, items, end = acting.play(s, lambda ev: 2.0)
            self.assertEqual([i[3] for i in items if i[0] == "scene"], [k]); self.assertGreater(end, 4)
    def test_unknown_spot_error_lists_this_scenes_spots(self):
        with self.assertRaises(Exception) as c: acting.play(parse_script(script_for("museum", ["moon base"])), lambda ev: 2.0)
        self.assertIn("painting", str(c.exception)); self.assertIn("museum", str(c.exception))
    def test_multiword_scene_names_work_in_header_and_directive(self):
        self.assertEqual(scenes.resolve("Train Station"), "train station"); self.assertEqual(scenes.resolve("gare"), "train station")
        acting.check(parse_script(script_for("train station", ["platform"])))
    def test_all_readme_scenes_exist(self):
        need = {"supermarket", "bookstore", "restaurant", "train station", "museum", "eiffel", "airport", "market", "library", "beach", "courtyard", "apartment"}
        self.assertFalse(need - set(scenes.SCENES), "missing scenes")
if __name__ == "__main__": unittest.main(verbosity=1)
