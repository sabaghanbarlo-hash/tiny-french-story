"""Reel cover (1080x1920). Title sits inside the centre band that stays visible when Instagram crops the cover for the profile grid."""
from PIL import Image, ImageDraw
from .config import *
from .fonts import font
from . import scenes as SC, rig
from .render import block, pill, wordmark

def make_cover(script, path):
    scene = SC.resolve(script.meta.get("scene", "street")) or "street"
    img = SC.background(scene); d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((0, 280, W, 860), fill=(255, 255, 255, 120))
    wordmark(d, 300); pill(d, W // 2, 420, "LEARN FRENCH", NAVY, size=36)
    title = script.meta.get("cover") or script.meta["title"]
    block(d, W // 2, 520, title.upper() if len(title) < 22 else title, 84, NAVY, 900, maxlines=3)
    base = dict(face=1, expr="happy", walking=0, phase=0, act=None, ap=0, item=None, bites=0, mouth=0.0, t=0.2)
    for n, x, face, act, ap in (("Camille", 300, 1, "wave", 0.3), ("Julien", 780, -1, None, 0)):
        spr = rig.draw(n, dict(base, face=face, act=act, ap=ap)); sc = 1.2
        spr = spr.resize((int(spr.width * sc), int(spr.height * sc)), Image.BILINEAR)
        img.paste(spr, (int(x - rig.CX * sc), int(1560 - rig.FY * sc)), spr)
    d.text((W // 2, 1640), "Small steps. Big dreams.", font=font(40, False), fill=NAVY, anchor="ma")
    img.save(path)
