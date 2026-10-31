"""Drawn characters for Tiny French: Adrien and Marinette (chibi, soft flat colours), animated by code."""
import functools, math
from PIL import Image, ImageDraw, ImageFilter

CHAR_SCALE = 0.9
SKIN = (253, 227, 203)
SKIN_SH = (240, 205, 178)
INK = (92, 52, 56)
CHARS = {
    "Adrien": dict(voice="fr-FR-HenriNeural", accent=(95, 158, 134), x=16),
    "Marinette": dict(voice="fr-FR-DeniseNeural", accent=(228, 140, 152), x=560),
    "Alia": dict(voice="fr-FR-DeniseNeural", accent=(205, 153, 54), x=16),
    "Nino": dict(voice="fr-FR-HenriNeural", accent=(54, 151, 145), x=560),
    "Chloé": dict(voice="fr-FR-DeniseNeural", accent=(181, 157, 224), x=16),
    "Lucas": dict(voice="fr-FR-HenriNeural", accent=(177, 91, 57), x=560),
    "Cat": dict(voice="fr-FR-HenriNeural", accent=(247, 190, 82), x=16),
    "Bugaboo": dict(voice="fr-FR-DeniseNeural", accent=(224, 45, 52), x=560),
}


def _bez(p0, p1, p2, n=14):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in [i / n for i in range(n + 1)]]


def lock_pts(root, ctrl, tip, width, n=14):
    """Pointed hair lock along a curve: thick in the middle, sharp at the tip."""
    c = _bez(root, ctrl, tip, n)
    left, right = [], []
    for i, (x, y) in enumerate(c):
        a = c[min(i + 1, n)]; b = c[max(i - 1, 0)]
        dx, dy = a[0] - b[0], a[1] - b[1]; L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        w = width * math.sin(math.pi * (0.12 + 0.88 * i / n) ** 0.9) * (1 - 0.15 * i / n) / 2
        if i == n:
            w = 0
        left.append((x + nx * w, y + ny * w)); right.append((x - nx * w, y - ny * w))
    return left + right[::-1]


def _eyes(d, P, S, blink, lash):
    for ex in (214, 346):
        if blink:
            d.arc(P(ex - 30, 346, ex + 30, 392), 200, 340, fill=(60, 34, 46), width=int(7 * S))
            if lash:
                side = -1 if ex < 280 else 1
                d.line(P(ex + side * 30, 372, ex + side * 42, 362), fill=(52, 28, 40), width=int(5 * S))
            continue
        d.ellipse(P(ex - 27, 318, ex + 27, 396), fill=(58, 30, 46))
        d.ellipse(P(ex - 20, 368, ex + 20, 394), fill=(108, 56, 70))
        d.ellipse(P(ex - 17, 328, ex + 4, 354), fill=(255, 255, 255))
        d.ellipse(P(ex + 6, 368, ex + 17, 380), fill=(255, 255, 255))
        d.arc(P(ex - 31, 312, ex + 31, 378), 195, 345, fill=(52, 28, 40), width=int(7 * S))
        if lash:
            side = -1 if ex < 280 else 1
            d.line(P(ex + side * 28, 344, ex + side * 44, 330), fill=(52, 28, 40), width=int(5 * S))


def _mouth(d, P, S, mouth):
    if mouth == 0:
        d.arc(P(262, 410, 298, 436), 15, 165, fill=INK, width=int(5 * S))
    elif mouth == 1:
        d.ellipse(P(268, 414, 292, 438), fill=(128, 48, 62))
    else:
        d.ellipse(P(260, 410, 300, 446), fill=(128, 48, 62)); d.ellipse(P(268, 430, 292, 444), fill=(238, 128, 140))


def _smooth(layer, S, r=5, thr=120):
    a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(r * S)).point(lambda v: 255 if v > thr else 0)
    layer.putalpha(a.filter(ImageFilter.GaussianBlur(0.8 * S)))
    return layer


@functools.lru_cache(None)
def _sprite_base(name, mouth, blink):
    S = 2 * CHAR_SCALE
    w, h = int(560 * S), int(760 * S)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    P = lambda *v: [int(x * S) for x in v]
    PP = lambda pts: [(x * S, y * S) for x, y in pts]
    ell = lambda box, fill, dd=None: (dd or d).ellipse(P(*box), fill=fill)
    poly = lambda pts, fill, dd=None: (dd or d).polygon(PP(pts), fill=fill)

    def layer(draw_fn, color, r=5):
        L = Image.new("RGBA", (w, h), color + (0,)); dd = ImageDraw.Draw(L); draw_fn(dd)
        L = Image.composite(Image.new("RGBA", (w, h), color + (255,)), L, L.getchannel("A"))
        return _smooth(L, S, r)

    def put(L):
        nonlocal im, d
        im = Image.alpha_composite(im, L); d = ImageDraw.Draw(im)

    def line(pts, col, width):
        d.line(PP(pts), fill=col, width=int(width * S), joint="curve")

    if name == "Adrien":
        gold, gold_d, gold_l = (247, 208, 120), (226, 170, 84), (255, 238, 176)
        # hair behind the head
        def back(dd):
            ell((112, 112, 448, 440), gold, dd)
            for pts in (lock_pts((150, 250), (100, 300), (74, 372), 70), lock_pts((410, 250), (462, 290), (486, 352), 64),
                        lock_pts((262, 124), (288, 76), (338, 58), 54)):
                poly(pts, gold, dd)
        put(layer(back, gold, 4))
        # body: white open jacket, black tee with rainbow stripes
        def jacket(dd):
            poly([(112, 600), (124, 540), (160, 494), (226, 466), (334, 466), (400, 494), (436, 540), (448, 600), (452, 760), (108, 760)], (244, 238, 238), dd)
        put(layer(jacket, (244, 238, 238), 6))
        tee = [(226, 490), (334, 490), (350, 760), (210, 760)]
        poly(tee, (42, 36, 42))
        xl = lambda y: 226 - 16 * (y - 490) / 270; xr = lambda y: 334 + 16 * (y - 490) / 270
        for i, c in enumerate(((110, 176, 120), (150, 108, 190), (244, 202, 100))):
            y0 = 640 + i * 26; y1 = y0 + 18
            poly([(xl(y0), y0), (xr(y0), y0), (xr(y1), y1), (xl(y1), y1)], c)
        poly([(240, 462), (320, 462), (280, 548)], SKIN)                                   # chest V
        poly([(240, 462), (262, 470), (252, 500)], SKIN_SH)
        poly([(214, 472), (246, 462), (238, 548), (198, 520)], (232, 224, 226)); poly([(346, 472), (314, 462), (322, 548), (362, 520)], (232, 224, 226))   # collar
        line([(176, 540), (196, 640)], (226, 216, 218), 4); line([(384, 540), (364, 640)], (226, 216, 218), 4)
        ell((130, 316, 180, 396), SKIN)                                                    # left ear
        ell((136, 154, 424, 462), SKIN)                                                    # face
        # fringe: big swoop from his right to his left
        def front(dd):
            poly([(118, 262), (124, 190), (196, 126), (330, 116), (432, 184), (442, 262), (430, 226), (300, 214), (180, 226)], gold, dd)
            for root, ctrl, tip, wd in (((400, 150), (420, 215), (392, 262), 66), ((340, 140), (330, 225), (296, 276), 70),
                                        ((276, 132), (240, 215), (206, 282), 76), ((206, 140), (166, 220), (150, 310), 74),
                                        ((140, 190), (118, 240), (124, 300), 50)):
                poly(lock_pts(root, ctrl, tip, wd), gold, dd)
        put(layer(front, gold, 2))
        for root, ctrl, tip in (((390, 150), (360, 200), (330, 232)), ((300, 140), (250, 190), (214, 236)), ((236, 132), (196, 180), (168, 232)), ((330, 120), (400, 150), (428, 214))):
            line(_bez(root, ctrl, tip, 10), gold_d, 6)
        for root, ctrl, tip in (((340, 130), (300, 150), (268, 178)), ((240, 126), (212, 146), (196, 176))):
            line(_bez(root, ctrl, tip, 8), gold_l, 5)
        d.arc(P(178, 296, 244, 324), 200, 340, fill=(206, 154, 88), width=int(5 * S)); d.arc(P(316, 290, 382, 318), 200, 340, fill=(206, 154, 88), width=int(5 * S))
        _eyes(d, P, S, blink, lash=False)
    else:
        navy, navy_d, navy_l = (50, 68, 122), (34, 46, 92), (92, 112, 170)
        def back(dd):
            ell((106, 106, 454, 440), navy, dd)
            poly(lock_pts((130, 250), (112, 360), (140, 470), 80), navy, dd); poly(lock_pts((430, 250), (448, 360), (420, 470), 80), navy, dd)
        put(layer(back, navy, 5))
        # body: charcoal jacket over white floral top
        def jacket(dd):
            poly([(150, 610), (160, 548), (186, 498), (240, 466), (320, 466), (374, 498), (400, 548), (410, 610), (414, 760), (146, 760)], (84, 74, 80), dd)
        put(layer(jacket, (84, 74, 80), 6))
        poly([(236, 474), (324, 474), (338, 760), (222, 760)], (242, 234, 234))
        ell((246, 446, 314, 520), SKIN)                                                    # neck / scoop neckline
        poly([(244, 462), (316, 462), (306, 500), (254, 500)], SKIN)
        poly([(226, 468), (252, 466), (264, 560), (240, 640), (212, 540)], (62, 54, 60)); poly([(334, 468), (308, 466), (296, 560), (320, 640), (348, 540)], (62, 54, 60))
        d.arc(P(244, 480, 316, 560), 20, 160, fill=(120, 110, 114), width=int(3 * S))
        for fx, fy in ((262, 640), (296, 660), (270, 690)):
            for ang in range(5):
                ax, ay = fx + 10 * math.cos(ang * 1.2566), fy + 10 * math.sin(ang * 1.2566)
                ell((ax - 7, ay - 7, ax + 7, ay + 7), (238, 150, 170))
            ell((fx - 4, fy - 4, fx + 4, fy + 4), (252, 220, 120))
        for lx, ly, rot in ((244, 668, 1), (300, 636, -1)):
            poly([(lx, ly), (lx + 16 * rot, ly - 8), (lx + 22 * rot, ly + 6)], (66, 80, 74))
        ell((136, 154, 424, 462), SKIN)
        # bangs: swept locks with a parting
        def front(dd):
            poly([(112, 270), (118, 196), (196, 124), (330, 114), (436, 186), (448, 270), (430, 250), (300, 240), (170, 255)], navy, dd)
            for root, ctrl, tip, wd in (((178, 134), (140, 240), (180, 346), 84), ((262, 126), (220, 210), (222, 300), 84),
                                        ((330, 126), (372, 200), (338, 292), 84), ((404, 140), (434, 220), (404, 300), 60)):
                poly(lock_pts(root, ctrl, tip, wd), navy, dd)
        put(layer(front, navy, 2))
        # pigtails with small red ties
        def tails(dd):
            ell((80, 470, 206, 650), navy, dd); ell((354, 470, 480, 650), navy, dd)
            poly(lock_pts((160, 440), (150, 470), (136, 520), 54), navy, dd); poly(lock_pts((400, 440), (410, 470), (424, 520), 54), navy, dd)
        put(layer(tails, navy, 6))
        ell((146, 456, 170, 486), (206, 54, 64)); ell((390, 456, 414, 486), (206, 54, 64))
        for root, ctrl, tip in (((170, 140), (130, 220), (168, 320)), ((260, 130), (222, 180), (232, 250)), ((406, 150), (432, 220), (404, 290))):
            line(_bez(root, ctrl, tip, 10), navy_l, 6)
        line(_bez((110, 520), (100, 570), (130, 620), 10), navy_l, 5); line(_bez((450, 520), (460, 570), (430, 620), 10), navy_l, 5)
        d.arc(P(178, 298, 244, 326), 200, 340, fill=navy_d, width=int(5 * S)); d.arc(P(316, 298, 382, 326), 200, 340, fill=navy_d, width=int(5 * S))
        _eyes(d, P, S, blink, lash=True)
    ell((166, 398, 210, 422), (252, 190, 190)); ell((350, 398, 394, 422), (252, 190, 190))   # small blush
    _mouth(d, P, S, mouth)
    return im.resize((int(560 * CHAR_SCALE), int(760 * CHAR_SCALE)), Image.LANCZOS)



def _new_character(name, mouth, blink):
    """The six newer cast designs, drawn like Adrien and Marinette: soft smoothed hair, rounded outfits, small cute details."""
    S = 2 * CHAR_SCALE
    w, h = int(560 * S), int(760 * S)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    P = lambda *v: [int(x * S) for x in v]
    PP = lambda pts: [(x * S, y * S) for x, y in pts]
    ell = lambda box, fill, dd=None: (dd or d).ellipse(P(*box), fill=fill)
    poly = lambda pts, fill, dd=None: (dd or d).polygon(PP(pts), fill=fill)
    mir = lambda pts: [(560 - x, y) for x, y in pts]

    def layer(draw_fn, color, r=5):
        L = Image.new("RGBA", (w, h), color + (0,)); dd = ImageDraw.Draw(L); draw_fn(dd)
        L = Image.composite(Image.new("RGBA", (w, h), color + (255,)), L, L.getchannel("A"))
        return _smooth(L, S, r)

    def put(L):
        nonlocal im, d
        im = Image.alpha_composite(im, L); d = ImageDraw.Draw(im)

    def line(pts, col, width):
        d.line(PP(pts), fill=col, width=int(width * S), joint="curve")

    def blob(pts, col, r=5):
        put(layer(lambda dd: poly(pts, col, dd), col, r))

    def locks(specs, col, r=2, base_poly=None, mirror=False):
        def f(dd):
            if base_poly: poly(mir(base_poly) if mirror else base_poly, col, dd)
            for root, ctrl, tip, wd in specs:
                if mirror: root, ctrl, tip = [(560 - x, y) for x, y in (root, ctrl, tip)]
                poly(lock_pts(root, ctrl, tip, wd), col, dd)
        put(layer(f, col, r))

    def streaks(specs, col, wd=5, mirror=False):
        for root, ctrl, tip in specs:
            if mirror: root, ctrl, tip = [(560 - x, y) for x, y in (root, ctrl, tip)]
            line(_bez(root, ctrl, tip, 10), col, wd)

    def brows(col, y=298, mirror=False):
        d.arc(P(178, y, 244, y + 28), 200, 340, fill=col, width=int(5 * S)); d.arc(P(316, y, 382, y + 28), 200, 340, fill=col, width=int(5 * S))

    BOY_BODY = [(112, 600), (124, 540), (160, 494), (226, 466), (334, 466), (400, 494), (436, 540), (448, 600), (452, 760), (108, 760)]
    GIRL_BODY = [(150, 610), (160, 548), (186, 498), (240, 466), (320, 466), (374, 498), (400, 548), (410, 610), (414, 760), (146, 760)]
    CROWN = [(118, 262), (124, 190), (196, 126), (330, 116), (432, 184), (442, 262), (430, 226), (300, 214), (180, 226)]
    BOY_FRINGE = (((400, 150), (420, 215), (392, 262), 66), ((340, 140), (330, 225), (296, 276), 70), ((276, 132), (240, 215), (206, 282), 76),
                  ((206, 140), (166, 220), (150, 310), 74), ((140, 190), (118, 240), (124, 300), 50))
    GIRL_CROWN = [(112, 270), (118, 196), (196, 124), (330, 114), (436, 186), (448, 270), (430, 250), (300, 240), (170, 255)]
    after = []
    skin_neck = lambda: (ell((246, 446, 314, 520), SKIN), poly([(244, 462), (316, 462), (306, 500), (254, 500)], SKIN))

    if name == "Alia":
        hair, hair_d, hair_l = (151, 70, 49), (112, 46, 38), (208, 120, 86)
        mus, mus_d, cream = (226, 178, 74), (176, 124, 44), (255, 240, 208)
        # soft bob that curls under at the ends
        def back(dd):
            ell((104, 104, 456, 448), hair, dd)
            poly(lock_pts((136, 250), (100, 360), (158, 452), 92), hair, dd); poly(lock_pts((424, 250), (460, 360), (402, 452), 92), hair, dd)
            ell((112, 410, 176, 486), hair, dd); ell((384, 410, 448, 486), hair, dd)
        put(layer(back, hair, 6))
        blob([(150, 610), (160, 548), (186, 498), (240, 466), (320, 466), (374, 498), (400, 548), (410, 610), (414, 760), (146, 760)], mus, 6)   # cardigan
        poly([(236, 474), (324, 474), (338, 760), (222, 760)], cream)
        skin_neck()
        blob([(230, 468), (282, 520), (262, 552), (212, 506)], (255, 252, 245), 4); blob([(330, 468), (278, 520), (298, 552), (348, 506)], (255, 252, 245), 4)   # round collar
        for by in (610, 650, 690): ell((296, by, 312, by + 16), mus_d)
        d.arc(P(330, 640, 396, 700), 200, 340, fill=mus_d, width=int(3 * S))
        ell((136, 154, 424, 462), SKIN)
        locks((((178, 134), (140, 240), (180, 346), 84), ((262, 126), (220, 210), (222, 300), 84), ((330, 126), (372, 200), (338, 292), 84), ((404, 140), (434, 220), (404, 300), 60)),
              hair, 2, base_poly=GIRL_CROWN)
        streaks((((170, 140), (130, 220), (168, 320)), ((260, 130), (222, 180), (232, 250)), ((406, 150), (432, 220), (404, 290))), hair_l, 6)
        for fx, fy in ((404, 206), ):                                   # little flower clip
            for k in range(5):
                a = k * 1.2566 - 1.57; ex, ey = fx + 17 * math.cos(a), fy + 17 * math.sin(a)
                ell((ex - 11, ey - 11, ex + 11, ey + 11), (255, 190, 206))
            ell((fx - 8, fy - 8, fx + 8, fy + 8), (255, 232, 140))
        brows(hair_l)
        for fx, fy in ((176, 410), (190, 420), (204, 412), (356, 412), (370, 420), (384, 410)): ell((fx - 3, fy - 3, fx + 3, fy + 3), (212, 140, 120))   # freckles
        def glasses():
            for ex in (214, 346): d.ellipse(P(ex - 38, 322, ex + 38, 394), outline=(120, 70, 52), width=int(5 * S))
            line([(252, 354), (308, 354)], (120, 70, 52), 5)
            for ex, sd in ((214, -1), (346, 1)):
                d.arc(P(ex - 30, 330, ex - 8, 352), 200, 260, fill=(255, 255, 255), width=int(3 * S))
        after.append(glasses)

    elif name == "Nino":
        hair, hair_d, hair_l = (86, 56, 40), (54, 36, 30), (140, 96, 68)
        teal, teal_d = (58, 160, 150), (36, 118, 112)
        def back(dd):
            ell((112, 112, 448, 440), hair, dd)
            for pts in (lock_pts((150, 250), (104, 300), (90, 364), 64), lock_pts((410, 250), (458, 296), (474, 350), 60),
                        lock_pts((250, 128), (234, 84), (284, 60), 52), lock_pts((330, 126), (356, 82), (402, 90), 48)):
                poly(pts, hair, dd)
        put(layer(back, hair, 4))
        blob(BOY_BODY, teal, 6)                                                              # hoodie
        blob([(196, 466), (364, 466), (378, 524), (280, 566), (182, 524)], teal_d, 5)         # hood
        blob([(176, 650), (384, 650), (404, 744), (156, 744)], teal_d, 6)                    # pocket
        for sx in (250, 310):
            line([(sx, 520), (sx - 4 + (sx - 280) // 10, 612)], (255, 250, 241), 5); ell((sx - 6 + (sx - 280) // 10, 608, sx + 6 + (sx - 280) // 10, 622), (255, 250, 241))
        skin_neck()
        ell((130, 316, 180, 396), SKIN); ell((136, 154, 424, 462), SKIN)
        locks(BOY_FRINGE, hair, 2, base_poly=CROWN, mirror=True)
        streaks((((390, 150), (360, 200), (330, 232)), ((300, 140), (250, 190), (214, 236)), ((236, 132), (196, 180), (168, 232))), hair_d, 6, mirror=True)
        streaks((((340, 130), (300, 150), (268, 178)), ((240, 126), (212, 146), (196, 176))), hair_l, 5, mirror=True)
        brows(hair_d)
        # soft headphones
        d.arc(P(104, 132, 456, 470), 196, 344, fill=(48, 52, 60), width=int(14 * S))
        for cx0 in (112, 448):
            ell((cx0 - 36, 288, cx0 + 36, 392), (48, 52, 60)); ell((cx0 - 22, 304, cx0 + 22, 376), (112, 124, 132)); ell((cx0 - 10, 322, cx0 + 10, 358), (170, 184, 190))

    elif name == "Chloé":
        hair, hair_d, hair_l = (170, 120, 76), (122, 82, 52), (222, 176, 126)
        lav, lav_d, cream = (182, 160, 226), (146, 124, 196), (250, 244, 255)
        def back(dd):
            ell((106, 106, 454, 440), hair, dd)
            poly(lock_pts((124, 250), (86, 470), (124, 690), 118), hair, dd); poly(lock_pts((436, 250), (474, 470), (436, 690), 118), hair, dd)
        put(layer(back, hair, 6))
        blob(GIRL_BODY, lav, 6)                                                              # sweater
        blob([(214, 468), (346, 468), (352, 520), (280, 548), (208, 520)], cream, 4)          # collar
        skin_neck()
        d.arc(P(236, 490, 324, 560), 20, 160, fill=lav_d, width=int(4 * S))
        for k in range(3): line([(190 + k * 4, 650 + k * 30), (370 - k * 4, 650 + k * 30)], lav_d, 3)
        ell((136, 154, 424, 462), SKIN)
        locks((((180, 136), (158, 226), (226, 294), 82), ((262, 126), (250, 212), (316, 280), 84), ((336, 128), (374, 196), (400, 252), 76), ((408, 142), (440, 214), (432, 284), 58)),
              hair, 2, base_poly=GIRL_CROWN)
        streaks((((170, 140), (140, 220), (190, 290)), ((262, 130), (240, 180), (270, 240)), ((406, 150), (432, 220), (410, 280))), hair_l, 6)
        def curtains(dd):                                                                   # long locks falling over the shoulders
            poly(lock_pts((142, 300), (104, 470), (140, 650), 74), hair, dd); poly(lock_pts((418, 300), (456, 470), (420, 650), 74), hair, dd)
        put(layer(curtains, hair, 5))
        streaks((((126, 420), (110, 520), (130, 620)), ((434, 420), (450, 520), (430, 620))), hair_l, 5)
        poly([(280, 512), (238, 490), (236, 540)], (244, 150, 180)); poly([(280, 512), (322, 490), (324, 540)], (244, 150, 180)); ell((268, 502, 292, 526), (232, 120, 156))   # neck bow
        brows(hair_d)
        for bx, sg in ((176, 1),):                                                          # bow hair clip
            poly([(bx, 196), (bx - 30, 176), (bx - 30, 216)], (244, 150, 180)); poly([(bx, 196), (bx + 30, 176), (bx + 30, 216)], (244, 150, 180)); ell((bx - 9, 187, bx + 9, 205), (232, 120, 156))

    elif name == "Lucas":
        hair, hair_d, hair_l = (40, 36, 42), (22, 20, 25), (92, 82, 88)
        rust, rust_d, cream, scarf = (178, 94, 60), (132, 64, 44), (255, 232, 204), (62, 120, 128)
        def back(dd):
            ell((110, 104, 450, 450), hair, dd)
            poly(lock_pts((130, 250), (112, 320), (140, 392), 70), hair, dd); poly(lock_pts((430, 250), (448, 320), (420, 392), 70), hair, dd)
            poly(lock_pts((272, 124), (288, 74), (338, 60), 52), hair, dd)
        put(layer(back, hair, 5))
        blob(BOY_BODY, rust, 6)                                                              # bomber jacket
        poly([(236, 470), (324, 470), (338, 760), (222, 760)], cream)
        blob([(204, 466), (252, 470), (246, 536), (196, 504)], rust_d, 4); blob([(356, 466), (308, 470), (314, 536), (364, 504)], rust_d, 4)   # ribbed collar
        skin_neck()
        blob([(212, 476), (348, 476), (360, 526), (280, 552), (200, 526)], scarf, 5)         # scarf
        blob([(266, 524), (318, 524), (334, 672), (284, 660)], scarf, 4)
        line([(276, 590), (326, 596)], (96, 150, 158), 5); line([(280, 622), (330, 628)], (96, 150, 158), 5)
        ell((136, 154, 424, 462), SKIN)
        locks((((190, 134), (150, 215), (170, 292), 80), ((262, 126), (232, 200), (236, 266), 80), ((330, 126), (352, 200), (330, 268), 80), ((404, 140), (434, 210), (414, 278), 62)),
              hair, 2, base_poly=GIRL_CROWN)
        streaks((((176, 140), (140, 214), (166, 280)), ((330, 130), (360, 190), (340, 250)), ((406, 150), (432, 214), (414, 268))), hair_l, 5)
        brows(hair_d, 300)
        ell((410, 384, 428, 404), (232, 188, 110))                                          # tiny gold earring

    elif name == "Cat":
        gold, gold_d, gold_l = (247, 192, 84), (222, 152, 56), (255, 224, 140)
        blk, blk_l = (36, 32, 40), (74, 68, 82)
        def back(dd):
            ell((112, 112, 448, 440), gold, dd)
            for pts in (lock_pts((150, 250), (100, 300), (74, 372), 70), lock_pts((410, 250), (462, 290), (486, 352), 64), lock_pts((262, 124), (288, 76), (338, 58), 54)):
                poly(pts, gold, dd)
        put(layer(back, gold, 4))
        blob(BOY_BODY, blk, 6)                                                               # black suit
        line([(190, 560), (176, 700)], blk_l, 4); line([(370, 560), (384, 700)], blk_l, 4); line([(280, 540), (280, 760)], blk_l, 4)
        blob([(218, 466), (342, 466), (334, 494), (226, 494)], (247, 208, 120), 5)           # gold collar
        ell((260, 478, 300, 520), (247, 208, 120)); d.arc(P(260, 478, 300, 520), 0, 360, fill=(190, 140, 50), width=int(3 * S))
        line([(268, 500), (292, 500)], (150, 100, 40), 3); ell((274, 506, 286, 516), (110, 70, 40))
        ell((130, 316, 180, 396), SKIN); ell((136, 154, 424, 462), SKIN)
        blob([(145, 325), (170, 290), (220, 300), (280, 325), (340, 300), (390, 290), (415, 325), (390, 385), (345, 390), (280, 370), (215, 390), (170, 385)], (30, 28, 36), 5)   # mask
        locks(BOY_FRINGE, gold, 2, base_poly=CROWN)
        streaks((((390, 150), (360, 200), (330, 232)), ((300, 140), (250, 190), (214, 236)), ((236, 132), (196, 180), (168, 232)), ((330, 120), (400, 150), (428, 214))), gold_d, 6)
        streaks((((340, 130), (300, 150), (268, 178)), ((240, 126), (212, 146), (196, 176))), gold_l, 5)
        put(layer(lambda dd: (poly([(132, 190), (150, 62), (250, 174), (268, 204), (176, 214)], blk, dd), poly([(332, 204), (350, 174), (444, 58), (456, 190), (408, 218)], blk, dd)), blk, 5))
        put(layer(lambda dd: (poly([(164, 178), (172, 100), (228, 174)], blk_l, dd), poly([(372, 178), (436, 100), (430, 184)], blk_l, dd)), blk_l, 3))

    else:  # Bugaboo
        navy, navy_d, navy_l = (48, 62, 114), (34, 44, 92), (92, 108, 168)
        red, red_d, dot = (222, 52, 58), (150, 28, 39), (38, 36, 48)
        def back(dd):
            ell((106, 106, 454, 440), navy, dd)
            poly(lock_pts((130, 250), (112, 360), (140, 470), 80), navy, dd); poly(lock_pts((430, 250), (448, 360), (420, 470), 80), navy, dd)
        put(layer(back, navy, 5))
        blob(GIRL_BODY, red, 6)                                                              # spotted suit
        for fx, fy in ((212, 560), (350, 560), (186, 650), (280, 620), (374, 650), (232, 710), (330, 716)): ell((fx - 14, fy - 14, fx + 14, fy + 14), dot)
        skin_neck()
        line([(280, 520), (280, 760)], red_d, 3)
        ell((136, 154, 424, 462), SKIN)
        blob([(145, 325), (170, 290), (220, 300), (280, 325), (340, 300), (390, 290), (415, 325), (390, 385), (345, 390), (280, 370), (215, 390), (170, 385)], (226, 48, 56), 5)   # mask
        locks((((178, 134), (140, 240), (180, 346), 84), ((262, 126), (220, 210), (222, 300), 84), ((330, 126), (372, 200), (338, 292), 84), ((404, 140), (434, 220), (404, 300), 60)),
              navy, 2, base_poly=GIRL_CROWN)
        def tails(dd):
            ell((80, 470, 206, 650), navy, dd); ell((354, 470, 480, 650), navy, dd)
            poly(lock_pts((160, 440), (150, 470), (136, 520), 54), navy, dd); poly(lock_pts((400, 440), (410, 470), (424, 520), 54), navy, dd)
        put(layer(tails, navy, 6))
        streaks((((170, 140), (130, 220), (168, 320)), ((260, 130), (222, 180), (232, 250)), ((406, 150), (432, 220), (404, 290))), navy_l, 6)
        streaks((((110, 520), (100, 570), (130, 620)), ((450, 520), (460, 570), (430, 620))), navy_l, 5)
        for bx, sg in ((158, -1), (402, 1)):                                                # soft red bows
            blob([(bx, 468), (bx + sg * 46, 440), (bx + sg * 40, 496)], red, 4); ell((bx - 14, 454, bx + 14, 482), red_d)
        brows(navy_d)

    _eyes(d, P, S, blink, lash=False)
    ell((166, 398, 210, 422), (252, 188, 188)); ell((350, 398, 394, 422), (252, 188, 188))
    _mouth(d, P, S, mouth)
    for fn in after: fn()
    return im.resize((int(560 * CHAR_SCALE), int(760 * CHAR_SCALE)), Image.LANCZOS)


@functools.lru_cache(maxsize=128)
def sprite(name, mouth, blink):
    """Render the eight cast designs; Adrien and Marinette remain unchanged."""
    if name in ("Adrien", "Marinette"):
        return _sprite_base(name, mouth, blink)
    if name in ("Alia", "Nino", "Chloé", "Lucas", "Cat", "Bugaboo"):
        return _new_character(name, mouth, blink)
    # A script may introduce its own characters. Reuse a matching base silhouette
    # while the script-specific profile supplies its voice and accent colour.
    profile = CHARS.get(name, {})
    base = "Adrien" if profile.get("voice", "fr-FR-HenriNeural").endswith("HenriNeural") else "Marinette"
    return _sprite_base(base, mouth, blink)
