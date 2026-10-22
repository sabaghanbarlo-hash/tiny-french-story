import sys, unittest
sys.path.insert(0, ".")
from tinyfr.parser import parse_script, ScriptError, Say, Direction, SceneChange
BASE = open("lessons/01-bakery.txt", encoding="utf-8").read()

class T(unittest.TestCase):
    def test_full_parse_and_accents(self):
        s = parse_script(BASE)
        self.assertEqual(s.meta["title"], "Camille et Julien à la boulangerie")
        says = [e for e in s.story if isinstance(e, Say)]
        self.assertEqual(len(says), 5)
        self.assertEqual(says[0].fr, "Bonjour ! Tu veux un croissant ?")
        self.assertEqual(says[1].fr, "Oui, s'il te plaît !")
        self.assertEqual(says[1].en, "Yes, please!")
    def test_directions_simultaneous_scene(self):
        s = parse_script(BASE)
        d = [e for e in s.story if isinstance(e, Direction)]
        self.assertTrue(d[1].simultaneous); self.assertFalse(d[0].simultaneous)
        self.assertEqual([e.place for e in s.story if isinstance(e, SceneChange)], ["bakery"])
        self.assertTrue(all(not isinstance(e, Say) or e.fr for e in s.story))
    def test_sections(self):
        s = parse_script(BASE)
        self.assertEqual(len(s.vocab), 3); self.assertEqual(s.vocab[1].term, "s'il te plaît")
        self.assertEqual(s.vocab[1].examples[0][0], "Un croissant, s'il te plaît.")
        self.assertEqual(len(s.grammar[0].examples), 2)
        self.assertEqual(s.quiz[0].answer, "B"); self.assertEqual(len(s.quiz[0].options), 3)
    def test_guillemet_wrapper_tolerated(self):
        t = BASE.replace("> Camille enters left", "\u00ab> Camille enters left").replace("Camille: Voilà ! | Here you go!", "Camille: Voilà ! | Here you go!\u00bb")
        s = parse_script(t)
        self.assertEqual([e for e in s.story if isinstance(e, Say)][2].en, "Here you go!")
    def test_french_quotes_inside_line_kept(self):
        t = BASE.replace("De rien ! | You're welcome!", "\u00ab De rien ! \u00bb dit-elle | She says \u2018you are welcome\u2019")
        s = parse_script(t)
        self.assertIn("\u00ab De rien", [e for e in s.story if isinstance(e, Say)][-1].fr)
    def test_errors(self):
        with self.assertRaises(ScriptError) as c: parse_script(BASE.replace("[grammar]", "[x]"))
        with self.assertRaises(ScriptError) as c: parse_script(BASE.replace("Hello! Do you want a croissant?", ""))
        self.assertIn("translation", str(c.exception))
        with self.assertRaises(ScriptError) as c: parse_script(BASE.replace("Julien: Oui", "Marie: Oui"))
        self.assertIn("unknown speaker", str(c.exception))
        with self.assertRaises(ScriptError) as c: parse_script(BASE.replace("> Camille looks happy", "Camille looks happy"))
        self.assertIn("directions must start", str(c.exception))
        with self.assertRaises(ScriptError) as c: parse_script(BASE.replace("Answer: B", "Answer: Z"))
        with self.assertRaises(ScriptError) as c: parse_script(BASE.replace("title: Camille et Julien à la boulangerie", ""))
        with self.assertRaises(ScriptError) as c: parse_script(BASE.split("[vocab]")[0])
if __name__ == "__main__": unittest.main(verbosity=2)
