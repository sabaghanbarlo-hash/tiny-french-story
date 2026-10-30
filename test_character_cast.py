import os, sys, unittest
sys.path.insert(0, ".")
from tinyfr.autodirect import parse_any
from tinyfr.acting import play
from tinyfr import faces, rig
from sprites import sprite
from small import parse_story

SCRIPT = """title: Camille et Théo au café
scene: cafe
cast: Camille, Théo
Camille: Bonjour ! | Hello!
Théo: Salut ! | Hi!
Camille: Je voudrais un café. | I would like a coffee.
Théo: Bien sûr ! | Of course!
vocab: bonjour | hello
"""

class CharacterCast(unittest.TestCase):
    def test_story_uses_selected_pair(self):
        script = parse_any(SCRIPT)
        stage, _, _ = play(script, lambda ev: 2.0)
        self.assertEqual(stage.names, ("Camille", "Théo"))

    def test_all_new_story_designs_render(self):
        for name in ("Camille", "Théo", "Chloé", "Lucas"):
            self.assertGreater(faces.head(name, "happy", 0, False, False).width, 0)
            self.assertGreater(rig.draw(name, dict(face=1, expr="happy", walking=0, phase=0, act=None, ap=0, item=None, bites=0, mouth=0, t=1)).height, 0)

    def test_small_mode_accepts_declared_cast(self):
        meta, lines, vocab = parse_story(SCRIPT)
        self.assertEqual(meta["cast"], "Camille, Théo")
        self.assertEqual({line["speaker"] for line in lines}, {"Camille", "Théo"})
        self.assertEqual(sprite("Camille", 0, False).size, sprite("Adrien", 0, False).size)

if __name__ == "__main__":
    unittest.main()
