import re, sys, unittest
sys.path.insert(0, ".")
import small

GREETING = re.compile(r"^\W*(bonjour|salut|coucou|bonsoir|hello|hi)\W*$", re.I)


def example_script():
    md = open("SMALL_DIRECTOR_PROMPT.md", encoding="utf-8").read()
    return re.search(r"## Example script\n```\n(.*?)\n```", md, re.S).group(1)


class SmallPrompt(unittest.TestCase):
    def test_example_is_valid_and_follows_the_opening_rule(self):
        meta, lines, vocab = small.parse_story(example_script())
        self.assertFalse(GREETING.match(lines[0]["fr"]), "the example must not open with a bare greeting")
        self.assertTrue(6 <= len(lines) <= 9, len(lines))
        self.assertTrue(3 <= len(vocab) <= 4, len(vocab))
        self.assertTrue(3 <= len(meta["title"].split()) <= 6, meta["title"])

    def test_caption_example_has_no_comment_ask(self):
        md = open("SMALL_DIRECTOR_PROMPT.md", encoding="utf-8").read()
        cap = re.search(r"## Example caption\n```\n(.*?)\n```", md, re.S).group(1)
        self.assertNotIn("omment", cap); self.assertIn("Send this", cap); self.assertLessEqual(len(cap), 2200)


if __name__ == "__main__":
    unittest.main()
