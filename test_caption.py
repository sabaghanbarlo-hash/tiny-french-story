import unittest
from tinyfr.meta import clean_caption


class CaptionGuard(unittest.TestCase):
    def test_strips_generator_notes(self):
        raw = "Saving Paris 🇫🇷 (This is your best post, so keep it simple!)\n\nSave this 💌"
        out = clean_caption(raw)
        self.assertNotIn("best post", out); self.assertNotIn("your", out); self.assertIn("Save this", out)

    def test_keeps_normal_parentheses(self):
        line = "• bonjour (hello) = hi"
        self.assertEqual(clean_caption(line), line)


if __name__ == "__main__":
    unittest.main()
