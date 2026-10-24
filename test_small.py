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


def test_characters_are_adrien_and_marinette():
    assert set(small.CHARS) == {"Adrien", "Marinette"}


def test_missing_english_reports_line_number():
    with pytest.raises(small.ScriptProblem, match="line 5"):
        small.parse_story(GOOD.replace("Bonjour ! | Hello!", "Bonjour !", 1))


def test_unknown_speaker_reports_line_number():
    with pytest.raises(small.ScriptProblem, match="line 5"):
        small.parse_story(GOOD.replace("Adrien: Bonjour !", "Camille: Bonjour !", 1))


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


def test_ref_sprite_is_none_without_assets(tmp_path, monkeypatch):
    import charart
    monkeypatch.setattr(charart, "ASSET_DIR", str(tmp_path))
    charart._load.cache_clear(); charart.ref_sprite.cache_clear()
    assert charart.ref_sprite("Adrien", 0, False) is None
    charart._load.cache_clear(); charart.ref_sprite.cache_clear()


def test_extract_and_animate_from_a_picture(tmp_path, monkeypatch):
    cv2 = pytest.importorskip("cv2")
    import numpy as np
    import charart
    img = np.full((1448, 1086, 3), (225, 238, 250), np.uint8)                 # cream wall (BGR)
    for cx, cy in ((290, 560), (810, 600)):
        cv2.ellipse(img, (cx, cy), (150, 170), 0, 0, 360, (203, 227, 253), -1)  # skin
        cv2.rectangle(img, (cx - 130, cy + 120), (cx + 130, 790), (200, 200, 210), -1)
    for ex, ey in ((256, 551), (371, 540), (742, 578), (858, 588)):
        cv2.ellipse(img, (ex, ey), (24, 30), 0, 0, 360, (46, 30, 58), -1)       # eyes
    cv2.ellipse(img, (316, 609), (14, 7), 0, 0, 180, (60, 40, 60), 3); cv2.ellipse(img, (796, 644), (14, 7), 0, 0, 180, (60, 40, 60), 3)
    ref = tmp_path / "ref.png"; cv2.imwrite(str(ref), img)
    meta = charart.extract(str(ref), str(tmp_path / "sprites"))
    assert set(meta) == {"Adrien", "Marinette"}
    monkeypatch.setattr(charart, "ASSET_DIR", str(tmp_path / "sprites"))
    charart._load.cache_clear(); charart.ref_sprite.cache_clear()
    base, blink, talk = charart.ref_sprite("Adrien", 0, False), charart.ref_sprite("Adrien", 0, True), charart.ref_sprite("Adrien", 2, False)
    assert base.size == blink.size == talk.size and base.width > 200
    assert base.tobytes() != blink.tobytes() and base.tobytes() != talk.tobytes()
    charart._load.cache_clear(); charart.ref_sprite.cache_clear()
