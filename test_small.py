import os, subprocess, sys, tempfile
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import small  # noqa: E402
from sprites import sprite  # noqa: E402

SAMPLE = os.path.join(HERE, "lessons", "small", "01-meeting-for-the-first-time.txt")
GOOD = open(SAMPLE, encoding="utf-8").read()


def run(*args):
    return subprocess.run([sys.executable, os.path.join(HERE, "small.py"), *args], capture_output=True, text=True, encoding="utf-8")


def test_parse_good_script_keeps_accents():
    meta, lines, vocab = small.parse_story(GOOD)
    assert meta["title"] == "Meeting for the First Time" and meta["episode"] == "1"
    assert len(lines) == 7 and len(vocab) == 5
    assert lines[2]["fr"].startswith("Enchanté") and lines[4]["fr"].endswith("s'il te plaît.")


def test_character_library_contains_all_eight_characters():
    expected = {"Adrien", "Marinette", "Alia", "Nino", "Chloé", "Lucas", "Cat", "Bugaboo"}
    assert set(small.CHARS) == expected
    assert all(entry["voice"].startswith("fr-FR-") for entry in small.CHARS.values())
    assert all(len(entry["accent"]) == 3 for entry in small.CHARS.values())


def test_missing_english_reports_line_number():
    with pytest.raises(small.ScriptProblem, match="line 5"):
        small.parse_story(GOOD.replace("Bonjour ! | Hello!", "Bonjour !", 1))


def test_unknown_speaker_reports_line_number():
    with pytest.raises(small.ScriptProblem, match="line 5"):
        small.parse_story(GOOD.replace("Adrien: Bonjour !", "Sophie: Bonjour !", 1))


def test_missing_title_and_no_dialogue_and_too_long():
    with pytest.raises(small.ScriptProblem, match="title"):
        small.parse_story("Adrien: Salut | Hi")
    with pytest.raises(small.ScriptProblem, match="dialogue"):
        small.parse_story("title: Vide")
    with pytest.raises(small.ScriptProblem, match="too long"):
        small.parse_story(GOOD + "# " + "x" * small.MAX_CHARS)


def test_bad_vocab_line():
    with pytest.raises(small.ScriptProblem, match="line"):
        small.parse_story(GOOD + "\nvocab: seulement\n")


def test_unknown_scene_and_auto_scene():
    meta, lines, _ = small.parse_story(GOOD.replace("scene: cafe", "scene: moon-base"))
    with pytest.raises(small.ScriptProblem, match="unknown scene"):
        small.pick_scene(meta, lines)
    meta, lines, _ = small.parse_story(GOOD.replace("scene: cafe\n", "").replace("café", "croissant"))
    assert small.pick_scene(meta, lines) == "bakery"
    for name in small.SCENES:
        bg, fg = small.make_scene(name, {"title": "Test", "episode": "1"})
        assert bg.size == (small.W, small.H)


def test_sprites_animate():
    a, b, c = sprite("Adrien", 0, False), sprite("Adrien", 2, False), sprite("Adrien", 0, True)
    assert a.tobytes() != b.tobytes() and a.tobytes() != c.tobytes()  # mouth shapes and blinking change the pixels
    assert sprite("Adrien", 0, False).tobytes() != sprite("Marinette", 0, False).tobytes()


def test_srt_time_and_caption():
    assert small.srt_time(3661.5) == "01:01:01,500"
    meta, lines, vocab = small.parse_story(GOOD)
    cap = small.caption(meta, vocab)
    assert "bonjour — hello" in cap and "#learnfrench" in cap


def test_check_cli_exit_codes():
    assert run("--check", SAMPLE).returncode == 0
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("title: X\nAdrien: pas d'anglais\n")
    r = run("--check", f.name); os.unlink(f.name)
    assert r.returncode == 1 and "::error" in r.stdout and "line 2" in r.stdout


def test_preview_frame_dimensions():
    from PIL import Image
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "p.png")
        r = run(SAMPLE, "--dummy-audio", "--preview", out)
        assert r.returncode == 0, r.stderr
        assert Image.open(out).size == (1080, 1920)


def test_all_places_render_and_can_be_chosen():
    assert len(small.SCENES) >= 14
    for name in small.SCENES:
        meta, lines, _ = small.parse_story(GOOD.replace("scene: cafe", "scene: " + name))
        assert small.pick_scene(meta, lines) == name
        bg, fg = small.make_scene(name, {"title": "Test", "episode": "1"})
        assert bg.size == (small.W, small.H) and fg.size[0] == small.W


def test_places_are_picked_automatically_from_the_words():
    cases = (("À l'aéroport : mon passeport, s'il vous plaît", "airport"), ("Au restaurant : l'addition, s'il vous plaît", "restaurant"),
             ("Au marché : combien coûtent les pommes ?", "market"), ("À la plage : le soleil", "beach"),
             ("À la bibliothèque : un livre", "library"), ("Au musée : un tableau", "museum"), ("Merci beaucoup, au revoir", "cafe"))
    for text, want in cases:
        meta, lines, _ = small.parse_story(f"title: Test\nscene: auto\nAdrien: {text} | x\n")
        assert small.pick_scene(meta, lines) == want, text


# ---- cover / thumbnail ----
def _cover(text=GOOD, scene=None):
    meta, lines, vocab = small.parse_story(text)
    meta["scene"] = scene or small.pick_scene(meta, lines)
    bg, fg = small.cover_scene(meta["scene"], meta)
    return small.make_cover(meta, lines, vocab, bg, fg)


def test_cover_is_a_full_size_thumbnail_for_every_place():
    for name in small.SCENES:
        img = _cover(scene=name)
        assert img.size == (small.W, small.H) and img.mode == "RGB"


def test_cover_has_its_own_title_panel_and_no_video_header_bar():
    from PIL import Image
    img = _cover()
    assert img.getpixel((90, 1300)) == (250, 248, 243)                       # cream title panel
    meta, lines, _ = small.parse_story(GOOD); meta["scene"] = "cafe"
    video_bg, _fg = small.make_scene("cafe", meta); cover_bg, _fg = small.cover_scene("cafe", meta)
    assert video_bg.getpixel((300, 150)) != cover_bg.getpixel((300, 150))   # the 'TINY FRENCH / Ep.1' bar is left out of the cover
    assert isinstance(img, Image.Image)


def test_every_lesson_gets_its_own_cover():
    other = GOOD.replace("title: Meeting for the First Time", "title: Ordering Coffee").replace("episode: 1", "episode: 2")
    assert _cover().tobytes() != _cover(other).tobytes()


def test_cover_title_fits_and_long_titles_shrink_then_cut():
    f, ls, size = small.cover_title("Meeting for the First Time")
    assert len(ls) <= 2 and all(f.getlength(x) <= 860 for x in ls) and size >= 88
    f, ls, size = small.cover_title("word " * 40)
    assert len(ls) <= 3 and ls[-1].endswith("…") and size == 60


def test_cover_line_gives_a_shorter_thumbnail_title():
    meta, _, _ = small.parse_story(GOOD.replace("episode: 1", "episode: 1\ncover: Meet Adrien"))
    assert meta["cover"] == "Meet Adrien"
    assert _cover(GOOD.replace("episode: 1", "episode: 1\ncover: Meet Adrien")).tobytes() != _cover().tobytes()


def test_cover_works_without_vocab_or_episode_and_with_five_long_words():
    _cover("title: Salut\nAdrien: Salut ! | Hi!\n")
    words = "".join(f"vocab: un très long mot numéro {i} | long word {i}\n" for i in range(5))
    img = _cover(GOOD.split("vocab:")[0] + words)
    assert img.size == (small.W, small.H)


def test_cover_cli_writes_a_png_without_voices_or_ffmpeg():
    from PIL import Image
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "c.png"); r = run(SAMPLE, "--cover", out)
        assert r.returncode == 0, r.stderr and Image.open(out).size == (1080, 1920)

