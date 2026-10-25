import sys
sys.path.insert(0, ".")
from tinyfr import faces, rig

NAMES = ("Adrien", "Marinette")


def test_expressions_blinking_and_talking_change_the_face():
    for n in NAMES:
        base = faces.head(n, "neutral").tobytes()
        for e in faces.EXPRESSIONS:
            assert faces.head(n, e).tobytes() != base, (n, e)
        assert faces.head(n, "neutral", 0.8).tobytes() != base
        assert faces.head(n, "neutral", 0, True).tobytes() != base
        assert faces.head(n, "neutral", 0, False, True).tobytes() != base


def test_unknown_expression_falls_back_to_neutral():
    assert faces.head("Adrien", "angry").tobytes() == faces.head("Adrien", "neutral").tobytes()


def test_the_two_characters_look_different_and_anchor_is_inside():
    a, m = faces.head("Adrien"), faces.head("Marinette")
    assert a.tobytes() != m.tobytes() and a.size == m.size
    assert 0 < faces.ANCHOR[0] < a.width and 0 < faces.ANCHOR[1] < a.height


def test_rig_draws_every_expression_for_both_characters():
    for n in NAMES:
        for e in ("neutral",) + faces.EXPRESSIONS:
            P = dict(face=1, expr=e, walking=0, phase=0, act=None, ap=0, item=None, bites=0, mouth=0.4, t=0.5)
            img = rig.draw(n, P)
            assert img.size == (rig.SW, rig.SH) and img.getbbox() is not None
        P = dict(face=-1, expr="happy", walking=1, phase=1.0, act="laugh", ap=0.3, item=None, bites=0, mouth=0, t=0.2)
        assert rig.draw(n, P).getbbox() is not None
