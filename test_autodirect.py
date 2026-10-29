import glob, sys, tempfile, unittest
sys.path.insert(0, ".")
from PIL import Image, ImageDraw
from tinyfr import acting, render, scenes as SC
from tinyfr.acting import NAMES, MIN_GAP
from tinyfr.autodirect import parse_any
from tinyfr.parser import Direction, SceneChange, Say, ScriptError

def plain(title, lines, scene=None, vocab=("bonjour | hello",)):
    head = f"title: {title}\n" + (f"scene: {scene}\n" if scene else "")
    return head + "\n" + "\n".join(lines) + "\n" + "".join(f"vocab: {v}\n" for v in vocab)

CAFE = ["Marinette: Bonjour ! Un café, s'il vous plaît. | Hello! A coffee, please.", "Adrien: Voilà ! | Here you go!", "Marinette: Merci ! | Thanks!"]

class AutoDirect(unittest.TestCase):
    def test_every_small_lesson_becomes_a_valid_story(self):
        for p in sorted(glob.glob("lessons/small/*.txt")):
            s = parse_any(open(p, encoding="utf-8").read()); acting.check(s)
            self.assertIsInstance(s.story[0], SceneChange)
    def test_place_follows_the_context(self):
        self.assertEqual(parse_any(plain("Au café", CAFE)).meta["scene"], "cafe")
        s = parse_any(plain("Le livre", ["Adrien: Je cherche un livre. | I am looking for a book.", "Marinette: Voici un livre. | Here is a book."]))
        self.assertEqual(s.meta["scene"], "bookstore")
        self.assertEqual(parse_any(plain("x", CAFE, scene="museum")).meta["scene"], "museum")
    def test_different_lessons_get_different_places(self):
        seen = {parse_any(plain(f"Lesson {i}", ["Adrien: Ah. | Ah.", "Marinette: Oui. | Yes."])).meta["scene"] for i in range(12)}
        self.assertGreaterEqual(len(seen), 4)
    def test_small_mode_places_have_a_story_scene(self):
        for name in ("airport", "beach", "apartment", "market", "library", "store"):
            self.assertIn(name, SC.ALIAS)
    def test_characters_walk_to_real_spots_of_the_scene(self):
        for p in sorted(glob.glob("lessons/small/*.txt")):
            s = parse_any(open(p, encoding="utf-8").read()); spots = SC.SCENES[s.meta["scene"]]["spots"]
            for e in s.story:
                if isinstance(e, Direction) and (" to " in e.text) and ("enters" in e.text or "walks" in e.text):
                    self.assertIn(e.text.split(" to ", 1)[1], spots, e.text)
    def test_standing_characters_keep_their_distance(self):
        for p in sorted(glob.glob("lessons/small/*.txt")):
            s = parse_any(open(p, encoding="utf-8").read()); st, items, end = acting.play(s, lambda ev: 2.0)
            t = 0.0
            while t < end:
                P = {n: st.pose(n, t) for n in NAMES}
                if all(P[n]["vis"] and not P[n]["moving"] for n in NAMES):
                    self.assertGreaterEqual(abs(P["Marinette"]["x"] - P["Adrien"]["x"]), MIN_GAP - 2, (p, t))
                t += 0.05
    def test_food_is_bought_after_the_reply_and_eaten_later(self):
        s = parse_any(plain("Croissant", ["Marinette: Un croissant, s'il vous plaît. | A croissant, please.", "Adrien: Voilà ! | Here!", "Marinette: Merci ! | Thanks!"], scene="bakery"))
        txt = [e.text if isinstance(e, Direction) else "SAY" for e in s.story]
        self.assertLess(txt.index("Marinette buys a croissant"), txt.index("Marinette eats the croissant"))
        self.assertEqual(txt[txt.index("Marinette buys a croissant") - 1], "SAY")
        self.assertGreater(txt.index("Marinette buys a croissant"), txt.index("SAY") + 1)
    def test_vocab_gets_an_example_from_the_dialogue(self):
        s = parse_any(plain("Au café", CAFE))
        self.assertEqual(s.vocab[0].term, "bonjour"); self.assertTrue(s.vocab[0].examples)
    def test_hand_directed_scripts_still_work(self):
        s = parse_any(open("lessons/03-un-croissant.txt", encoding="utf-8").read()); self.assertTrue(s.grammar and s.quiz)
    def test_errors_are_readable(self):
        with self.assertRaises(ScriptError): parse_any("title: x\n\nBob: Hi | Hi\n")
        with self.assertRaises(ScriptError): parse_any("title: x\nscene: moon\n\nAdrien: Salut | Hi\n")

class VocabAndBrand(unittest.TestCase):
    def test_vocab_is_spoken_french_means_english_french(self):
        s = parse_any(plain("Au café", CAFE, vocab=("bonjour | hello",)))
        with tempfile.TemporaryDirectory() as tmp:
            segs, mix, cues, skipped, end = render.build(s, tmp, dummy=True, sections=("vocab",))
        v = next(g for g in segs if g["kind"] == "vocab")
        inside = [m for m in mix if v["t0"] <= m[0] < v["t1"]]
        self.assertGreaterEqual(len(inside), 4)    # term, "means hello", term again, example sentence
        self.assertEqual(v["meaning"], "hello")
    def test_brand_tag_stays_above_the_shop_signs(self):
        im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); render.brand_tag(ImageDraw.Draw(im))
        self.assertLess(im.getbbox()[3], 215)

if __name__ == "__main__": unittest.main()
