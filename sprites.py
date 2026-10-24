"""Drawn characters for Tiny French "Small" videos: Adrien and Marinette."""
import functools, math
from PIL import Image, ImageDraw, ImageFilter

CHAR_SCALE = 0.9
SKIN = (253, 227, 203)
INK = (92, 52, 56)
CHARS = {
    "Adrien": dict(voice="fr-FR-HenriNeural", accent=(95, 158, 134), x=16),
    "Marinette": dict(voice="fr-FR-DeniseNeural", accent=(228, 140, 152), x=1080 - 16 - int(560 * CHAR_SCALE)),
}


def _eyes(d, P, S, blink, lash, ex_list=(218, 342)):
    for ex in ex_list:
        if blink:
            d.arc(P(ex - 30, 350, ex + 30, 392), 200, 340, fill=(60, 34, 46), width=int(7 * S))
            continue
        d.ellipse(P(ex - 27, 322, ex + 27, 396), fill=(58, 30, 46))
        d.ellipse(P(ex - 20, 366, ex + 22, 394), fill=(104, 52, 66))
        d.ellipse(P(ex - 17, 331, ex + 3, 357), fill=(255, 255, 255))
        d.ellipse(P(ex + 6, 366, ex + 17, 378), fill=(255, 255, 255))
        d.arc(P(ex - 31, 316, ex + 31, 380), 195, 345, fill=(52, 28, 40), width=int(7 * S))
        if lash:
            side = -1 if ex < 280 else 1
            ox = ex + side * 28
            d.line(P(ox, 340, ox + side * 14, 328), fill=(52, 28, 40), width=int(5 * S))


def _mouth(d, P, S, mouth):
    if mouth == 0:
        d.arc(P(262, 408, 298, 436), 15, 165, fill=INK, width=int(5 * S))
    elif mouth == 1:
        d.ellipse(P(266, 412, 294, 438), fill=(128, 48, 62))
    else:
        d.ellipse(P(258, 410, 302, 448), fill=(128, 48, 62)); d.ellipse(P(266, 430, 294, 446), fill=(238, 128, 140))


def _smooth(layer, S, r=5):
    a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(r * S)).point(lambda v: 255 if v > 120 else 0)
    layer.putalpha(a.filter(ImageFilter.GaussianBlur(0.8 * S)))
    return layer


@functools.lru_cache(None)
def sprite(name, mouth, blink):
    S = 2 * CHAR_SCALE
    w, h = int(560 * S), int(760 * S)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    P = lambda *v: [int(x * S) for x in v]
    ell = lambda box, fill, dd=None: (dd or d).ellipse(P(*box), fill=fill)
    poly = lambda pts, fill, dd=None: (dd or d).polygon(P(*[c for p in pts for c in p]), fill=fill)

    def layer(draw_fn, r=5, color=(0, 0, 0)):
        L = Image.new("RGBA", (w, h), color + (0,)); dd = ImageDraw.Draw(L); draw_fn(dd)
        L = Image.composite(Image.new("RGBA", (w, h), color + (255,)), L, L.getchannel("A"))
        return _smooth(L, S, r)

    if name == "Adrien":
        gold, gold_d, gold_l = (247, 208, 120), (228, 172, 86), (255, 236, 170)
        def back(dd):
            ell((108, 116, 452, 440), gold, dd)
            for cx, cy, r in ((116, 300, 40), (100, 366, 30), (444, 300, 40), (460, 366, 30), (160, 150, 46), (400, 150, 46), (280, 124, 54)):
                ell((cx - r, cy - r, cx + r, cy + r), gold, dd)
            poly([(236, 130), (272, 70), (316, 130)], gold, dd)
        im = Image.alpha_composite(im, layer(back, 7, gold)); d = ImageDraw.Draw(im)
        d.rounded_rectangle(P(160, 458, 400, 720), radius=int(60 * S), fill=(40, 34, 40))
        for i, c in enumerate(((110, 176, 120), (150, 108, 190), (244, 202, 100))):
            d.rectangle(P(205, 600 + i * 24, 355, 618 + i * 24), fill=c)
        poly([(150, 470), (232, 470), (238, 560), (228, 720), (140, 720), (128, 560)], (244, 238, 238))
        poly([(410, 470), (328, 470), (322, 560), (332, 720), (420, 720), (432, 560)], (244, 238, 238))
        poly([(232, 470), (250, 470), (240, 540)], (224, 212, 214)); poly([(328, 470), (310, 470), (320, 540)], (224, 212, 214))
        ell((118, 500, 192, 660), (246, 240, 240)); ell((368, 500, 442, 660), (246, 240, 240))
        poly([(246, 456), (314, 456), (280, 510)], SKIN)
        ell((134, 150, 426, 462), SKIN)
        def front(dd):
            dd.pieslice(P(116, 120, 444, 400), 180, 360, fill=gold)
            for cx, cy, r in ((160, 252, 40), (222, 232, 46), (292, 222, 46), (356, 234, 42), (410, 256, 34)):
                ell((cx - r, cy - r, cx + r, cy + r), gold, dd)
            poly([(116, 240), (80, 310), (146, 316)], gold, dd); poly([(444, 240), (482, 308), (418, 312)], gold, dd)
        im = Image.alpha_composite(im, layer(front, 4, gold)); d = ImageDraw.Draw(im)
        for box, a0, a1 in (((165, 140, 400, 300), 212, 252), ((205, 124, 440, 290), 285, 325)):
            d.arc(P(*box), a0, a1, fill=gold_d, width=int(9 * S))
        d.arc(P(195, 148, 330, 240), 225, 262, fill=gold_l, width=int(8 * S))
        d.arc(P(180, 300, 244, 330), 200, 340, fill=(214, 162, 92), width=int(5 * S)); d.arc(P(316, 300, 380, 330), 200, 340, fill=(214, 162, 92), width=int(5 * S))
        _eyes(d, P, S, blink, lash=False)
    else:
        navy, navy_d, navy_l = (50, 68, 122), (34, 46, 92), (88, 108, 166)
        def back(dd):
            ell((104, 102, 456, 440), navy, dd)
            ell((108, 250, 176, 480), navy, dd); ell((384, 250, 452, 480), navy, dd)
        im = Image.alpha_composite(im, layer(back, 7, navy)); d = ImageDraw.Draw(im)
        d.rounded_rectangle(P(160, 458, 400, 720), radius=int(60 * S), fill=(238, 228, 228))
        poly([(150, 470), (236, 470), (250, 560), (232, 720), (140, 720), (126, 560)], (78, 68, 74))
        poly([(410, 470), (324, 470), (310, 560), (328, 720), (420, 720), (434, 560)], (78, 68, 74))
        poly([(236, 470), (252, 470), (262, 520), (250, 560)], (60, 52, 58)); poly([(324, 470), (308, 470), (298, 520), (310, 560)], (60, 52, 58))
        d.arc(P(235, 462, 325, 540), 20, 160, fill=(70, 60, 66), width=int(4 * S))
        for fx, fy in ((268, 610), (296, 632), (276, 660)):
            for ang in range(5):
                ax, ay = fx + 11 * math.cos(ang * 1.2566), fy + 11 * math.sin(ang * 1.2566)
                ell((ax - 8, ay - 8, ax + 8, ay + 8), (240, 150, 170))
            ell((fx - 5, fy - 5, fx + 5, fy + 5), (252, 220, 120))
        ell((258, 640, 272, 654), (70, 84, 78)); ell((300, 612, 314, 626), (70, 84, 78))
        ell((118, 500, 192, 660), (86, 76, 82)); ell((368, 500, 442, 660), (86, 76, 82))
        poly([(246, 456), (314, 456), (280, 508)], SKIN)
        ell((124, 324, 170, 400), SKIN); ell((390, 324, 436, 400), SKIN)
        ell((134, 154, 426, 462), SKIN)
        def front(dd):
            poly([(122, 270), (130, 196), (210, 124), (330, 118), (430, 190), (444, 280), (424, 236), (350, 202), (270, 214), (214, 268), (186, 336), (150, 310)], navy, dd)
        im = Image.alpha_composite(im, layer(front, 4, navy)); d = ImageDraw.Draw(im)
        def tails(dd):
            ell((74, 440, 196, 610), navy, dd); ell((364, 440, 486, 610), navy, dd)
            ell((120, 420, 190, 500), navy, dd); ell((370, 420, 440, 500), navy, dd)
        im = Image.alpha_composite(im, layer(tails, 6, navy)); d = ImageDraw.Draw(im)
        ell((150, 436, 192, 480), (208, 54, 64)); ell((368, 436, 410, 480), (208, 54, 64))
        for box, a0, a1 in (((150, 134, 420, 290), 200, 250), ((190, 112, 440, 282), 282, 336)):
            d.arc(P(*box), a0, a1, fill=navy_l, width=int(8 * S))
        d.arc(P(86, 456, 190, 600), 110, 160, fill=navy_l, width=int(6 * S)); d.arc(P(370, 456, 474, 600), 20, 70, fill=navy_l, width=int(6 * S))
        d.arc(P(180, 304, 242, 334), 200, 340, fill=navy_d, width=int(5 * S)); d.arc(P(318, 304, 380, 334), 200, 340, fill=navy_d, width=int(5 * S))
        _eyes(d, P, S, blink, lash=True)
    ell((158, 394, 214, 428), (250, 170, 172)); ell((346, 394, 402, 428), (250, 170, 172))
    _mouth(d, P, S, mouth)
    return im.resize((int(560 * CHAR_SCALE), int(760 * CHAR_SCALE)), Image.LANCZOS)
