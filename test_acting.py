import sys, unittest
sys.path.insert(0, ".")
from tinyfr.parser import parse_script, ScriptError, Say
from tinyfr import acting
from tinyfr.acting import parse_dir, NAMES, MIN_GAP, W
L2 = open("lessons/02-journee-a-paris.txt", encoding="utf-8").read()
L1 = open("lessons/01-bakery.txt", encoding="utf-8").read()

def run(text, sec=2.0):
    s = parse_script(text); return acting.play(s, lambda ev: sec)

class Dir(unittest.TestCase):
    def test_variants(self):
        self.assertEqual([o.who for o in parse_dir("Both walk to counter")], ["Marinette", "Adrien"])
        self.assertEqual(parse_dir("Marinette enters left")[0].arg, "left")
        self.assertEqual(parse_dir("Adrien buys a croissant.")[0].arg, "croissant")
        self.assertEqual(parse_dir("Marinette gives the coffee to Adrien")[0].arg, "coffee|Adrien")
        self.assertEqual(parse_dir("wait 1.5")[0].arg, "1.5")
        self.assertEqual(parse_dir("Adrien picks up the map")[0].arg, "map")
    def test_errors(self):
        for bad, frag in (("Marinette dances", "unsupported direction"), ("Adrien buys a sword", "unsupported item"), ("Marinette looks angry", "unsupported feeling"), ("Marie waves", "must start with")):
            with self.assertRaises(ScriptError) as c: parse_dir(bad, 3)
            self.assertIn(frag, str(c.exception)); self.assertIn("line 3", str(c.exception))
    def test_stage_errors(self):
        with self.assertRaises(ScriptError) as c: run(L1.replace("> Marinette buys a croissant", "> Marinette buys a book").replace("> Marinette gives the croissant to Adrien", "> Marinette eats"))
        self.assertIn("cannot be eaten", str(c.exception))
        with self.assertRaises(ScriptError): run(L1.replace("> Marinette buys a croissant", "> Marinette gives it to Adrien"))
        with self.assertRaises(ScriptError) as c: run(L1.replace("> Marinette looks happy", "> Marinette enters left"))
        self.assertIn("already on stage", str(c.exception))
        with self.assertRaises(ScriptError) as c: run(L1.replace("@scene bakery", "@scene moon"))
        self.assertIn("unknown scene", str(c.exception))
        with self.assertRaises(ScriptError) as c: run(L1.replace("> Marinette buys a croissant", "> Marinette walks to the moon"))
        self.assertIn("Spots here", str(c.exception))
        with self.assertRaises(ScriptError) as c: run(L1.replace("> Marinette looks happy", "> Marinette exits left\n> Marinette waves"))
        self.assertIn("not on stage", str(c.exception))

class Inv(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.st, cls.items, cls.end = run(L2)
    def test_scenes_and_order(self):
        self.assertEqual([i[3] for i in self.items if i[0] == "scene"], ["street", "bakery", "cafe", "park"])
    def test_no_standing_on_each_other(self):
        bad = []; t = 2.6
        while t < self.end:
            p = {n: self.st.pose(n, t) for n in NAMES}
            if all(p[n]["vis"] for n in NAMES) and abs(p["Marinette"]["x"] - p["Adrien"]["x"]) < MIN_GAP - 2:
                movers = [n for n in NAMES if p[n]["moving"]]
                if not movers or not any(p[n]["lane"] < -20 for n in movers): bad.append(round(t, 2))
            t += 0.04
        self.assertEqual(bad, [])
    def test_items_follow_story(self):
        st = self.st; item = lambda n, t: st.pose(n, t)["item"]
        gives = [a for a in st.acts["Adrien"] if a[2] == "give"]; self.assertEqual(len(gives), 1)
        g0 = gives[0][0]
        self.assertEqual(item("Adrien", g0 + 0.5), "coffee"); self.assertIsNone(item("Adrien", g0 + 0.9)); self.assertEqual(item("Marinette", g0 + 0.9), "coffee")
        eats = [a for a in st.acts["Marinette"] if a[2] == "eat"]; self.assertEqual(len(eats), 1)
        self.assertEqual(item("Marinette", eats[0][0] + 0.1), "croissant"); self.assertIsNone(item("Marinette", eats[0][1] + 0.1))
        self.assertIsNone(item("Adrien", self.end - 0.1))
    def test_motion_is_continuous_no_teleport(self):
        cuts = [i[1] for i in self.items if i[0] == "scene"]
        for n in NAMES:
            prev = None; t = 2.6
            while t < self.end:
                P = self.st.pose(n, t); x = P["x"]
                if prev is not None and not any(abs(t - c) < 0.05 for c in cuts) and P["vis"] and abs(x - prev) > 40:
                    self.fail(f"{n} jumped {abs(x-prev):.0f}px at t={t:.2f}")
                prev = x; t += 0.04
    def test_nobody_speaks_during_actions(self):
        spans = sorted((i[1], i[2]) for i in self.items if i[0] in ("act", "say"))
        for (a0, a1), (b0, b1) in zip(spans, spans[1:]): self.assertLessEqual(a1, b0 + 1e-6)
    def test_speakers_face_each_other_when_idle(self):
        t = [i for i in self.items if i[0] == "say"][2][1] + 0.3
        p = {n: self.st.pose(n, t) for n in NAMES}
        self.assertEqual(p["Marinette"]["face"], 1 if p["Adrien"]["x"] > p["Marinette"]["x"] else -1)
    def test_characters_leave_and_scale(self):
        end = self.st.pose("Adrien", self.end - 0.1); self.assertFalse(end["vis"])
        for t in (4.0, 20.0, 60.0):
            for n in NAMES: self.assertGreaterEqual(self.st.pose(n, t)["lane"], -70.01)

class Cov(unittest.TestCase):
    def test_every_scene_item_expression_renders(self):
        from tinyfr import rig, scenes, items
        for k in scenes.SCENES: self.assertEqual(scenes.background(k).size, (1080, 1920))
        base = dict(face=1, expr="neutral", walking=0, phase=0, act=None, ap=0, item=None, bites=0, mouth=0, t=0.3)
        for n in NAMES:
            for e in sorted(set(acting.EXPRS.values())): rig.draw(n, dict(base, expr=e))
            for it in items.ITEMS: rig.draw(n, dict(base, item=it))
            for a in ("wave", "jump", "laugh", "nod", "cheer", "eat", "drink", "give", "bend", "hop"): rig.draw(n, dict(base, act=a, ap=0.4, item="croissant"))
if __name__ == "__main__": unittest.main(verbosity=1)
