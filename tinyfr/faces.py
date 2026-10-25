"""Heads for Story mode: the same Adrien and Marinette as the Small videos (same hair, eyes, bangs, ties),
with the Story expressions (happy, excited, surprised, sad, worried, confused, embarrassed, shy), blinking and talking.

head(name, expr, mouth, blink, laugh) -> RGBA image, face centre at ANCHOR.
"""
import functools, math
from PIL import Image, ImageDraw, ImageFilter

S = 2                          # supersampling while drawing
SCALE = 0.767                  # final size relative to the 560-wide design canvas
CROP = (60, 40, 500, 690)      # part of the design canvas that holds head, hair and pigtails
FACE_C = (280, 308)
ANCHOR = (int((FACE_C[0] - CROP[0]) * SCALE), int((FACE_C[1] - CROP[1]) * SCALE))
SKIN = (253, 227, 203)
INK = (92, 52, 56)
MOUTH = (128, 48, 62)
TONGUE = (238, 128, 140)
HAIR = {"Adrien": dict(main=(247, 208, 120), dark=(226, 170, 84), light=(255, 238, 176), brow=(206, 154, 88)),
        "Marinette": dict(main=(50, 68, 122), dark=(34, 46, 92), light=(92, 112, 170), brow=(34, 46, 92), tie=(206, 54, 64))}
BLUSH_EXPR = ("embarrassed", "shy", "happy", "excited")
EXPRESSIONS = ("happy", "excited", "surprised", "sad", "worried", "confused", "embarrassed", "shy")


def _bez(p0, p1, p2, n=14):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in [i / n for i in range(n + 1)]]


def _lock(root, ctrl, tip, width, n=14):
    c = _bez(root, ctrl, tip, n)
    left, right = [], []
    for i, (x, y) in enumerate(c):
        a = c[min(i + 1, n)]; b = c[max(i - 1, 0)]
        dx, dy = a[0] - b[0], a[1] - b[1]; L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        w = 0 if i == n else width * math.sin(math.pi * (0.12 + 0.88 * i / n) ** 0.9) * (1 - 0.15 * i / n) / 2
        left.append((x + nx * w, y + ny * w)); right.append((x - nx * w, y - ny * w))
    return left + right[::-1]


def _smooth(layer, r):
    a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(r * S)).point(lambda v: 255 if v > 120 else 0)
    layer.putalpha(a.filter(ImageFilter.GaussianBlur(0.8 * S)))
    return layer


class _Canvas:
    def __init__(self):
        self.w, self.h = 560 * S, 760 * S
        self.im = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0)); self.d = ImageDraw.Draw(self.im)

    P = staticmethod(lambda *v: [int(x * S) for x in v])
    PP = staticmethod(lambda pts: [(x * S, y * S) for x, y in pts])

    def ell(self, box, fill, dd=None): (dd or self.d).ellipse(self.P(*box), fill=fill)
    def poly(self, pts, fill, dd=None): (dd or self.d).polygon(self.PP(pts), fill=fill)
    def line(self, pts, col, width): self.d.line(self.PP(pts), fill=col, width=int(width * S), joint="curve")

    def layer(self, fn, color, r):
        L = Image.new("RGBA", (self.w, self.h), color + (0,)); fn(ImageDraw.Draw(L))
        L = Image.composite(Image.new("RGBA", (self.w, self.h), color + (255,)), L, L.getchannel("A"))
        self.im = Image.alpha_composite(self.im, _smooth(L, r)); self.d = ImageDraw.Draw(self.im)


@functools.lru_cache(None)
def _static(name):
    """Hair, ears, face and fringe: everything that does not move."""
    cv = _Canvas(); h = HAIR[name]; g = h["main"]
    if name == "Adrien":
        def back(dd):
            cv.ell((112, 112, 448, 440), g, dd)
            for pts in (_lock((150, 250), (100, 300), (74, 372), 70), _lock((410, 250), (462, 290), (486, 352), 64), _lock((262, 124), (288, 76), (338, 58), 54)):
                cv.poly(pts, g, dd)
        cv.layer(back, g, 4)
        cv.ell((130, 316, 180, 396), SKIN); cv.ell((136, 154, 424, 462), SKIN)
        def front(dd):
            cv.poly([(118, 262), (124, 190), (196, 126), (330, 116), (432, 184), (442, 262), (430, 226), (300, 214), (180, 226)], g, dd)
            for root, ctrl, tip, wd in (((400, 150), (420, 215), (392, 262), 66), ((340, 140), (330, 225), (296, 276), 70), ((276, 132), (240, 215), (206, 282), 76),
                                        ((206, 140), (166, 220), (150, 310), 74), ((140, 190), (118, 240), (124, 300), 50)):
                cv.poly(_lock(root, ctrl, tip, wd), g, dd)
        cv.layer(front, g, 2)
        for root, ctrl, tip in (((390, 150), (360, 200), (330, 232)), ((300, 140), (250, 190), (214, 236)), ((236, 132), (196, 180), (168, 232)), ((330, 120), (400, 150), (428, 214))):
            cv.line(_bez(root, ctrl, tip, 10), h["dark"], 6)
        for root, ctrl, tip in (((340, 130), (300, 150), (268, 178)), ((240, 126), (212, 146), (196, 176))):
            cv.line(_bez(root, ctrl, tip, 8), h["light"], 5)
    else:
        def back(dd):
            cv.ell((106, 106, 454, 440), g, dd)
            cv.poly(_lock((130, 250), (112, 360), (140, 470), 80), g, dd); cv.poly(_lock((430, 250), (448, 360), (420, 470), 80), g, dd)
        cv.layer(back, g, 5)
        cv.ell((136, 154, 424, 462), SKIN)
        def front(dd):
            cv.poly([(112, 270), (118, 196), (196, 124), (330, 114), (436, 186), (448, 270), (430, 250), (300, 240), (170, 255)], g, dd)
            for root, ctrl, tip, wd in (((178, 134), (140, 240), (180, 346), 84), ((262, 126), (220, 210), (222, 300), 84),
                                        ((330, 126), (372, 200), (338, 292), 84), ((404, 140), (434, 220), (404, 300), 60)):
                cv.poly(_lock(root, ctrl, tip, wd), g, dd)
        cv.layer(front, g, 2)
        def tails(dd):
            cv.ell((80, 470, 206, 650), g, dd); cv.ell((354, 470, 480, 650), g, dd)
            cv.poly(_lock((160, 440), (150, 470), (136, 520), 54), g, dd); cv.poly(_lock((400, 440), (410, 470), (424, 520), 54), g, dd)
        cv.layer(tails, g, 6)
        cv.ell((146, 456, 170, 486), h["tie"]); cv.ell((390, 456, 414, 486), h["tie"])
        for root, ctrl, tip in (((170, 140), (130, 220), (168, 320)), ((260, 130), (222, 180), (232, 250)), ((406, 150), (432, 220), (404, 290))):
            cv.line(_bez(root, ctrl, tip, 10), h["light"], 6)
        cv.line(_bez((110, 520), (100, 570), (130, 620), 10), h["light"], 5); cv.line(_bez((450, 520), (460, 570), (430, 620), 10), h["light"], 5)
    return cv.im


def _brow(cv, name, ex, side, lift, inner, arch):
    by = 306 - lift
    outer = (ex + side * 34, by + 8); inn = (ex - side * 34, by + 8 - inner)
    cv.line(_bez(outer, (ex, by - 12 - arch), inn, 10), HAIR[name]["brow"], 5)


@functools.lru_cache(maxsize=512)
def _head(name, expr, mq, blink, laugh):
    cv = _Canvas(); cv.im = _static(name).copy(); cv.d = ImageDraw.Draw(cv.im); d = cv.d; P = cv.P
    m = mq / 6.0
    closed = blink or laugh or expr == "embarrassed"
    happy_eyes = expr == "happy"
    big = expr in ("surprised", "excited")
    bl = expr in BLUSH_EXPR
    pad = 4 if bl else 0; col = (250, 160, 168) if bl else (252, 190, 190)
    cv.ell((166 - pad, 398 - pad // 2, 210 + pad, 422 + pad // 2), col); cv.ell((350 - pad, 398 - pad // 2, 394 + pad, 422 + pad // 2), col)
    oy = 8 if expr in ("sad", "shy") else 0
    for ex in (214, 346):
        if closed or happy_eyes:
            d.arc(P(ex - 30, 346 + oy, ex + 30, 392 + oy), 200, 340, fill=(60, 34, 46), width=int(7 * S))
            if name == "Marinette":
                sd = -1 if ex < 280 else 1
                d.line(P(ex + sd * 30, 372, ex + sd * 42, 362), fill=(52, 28, 40), width=int(5 * S))
            continue
        k = 1.12 if big else 1.0
        cy = 357 + oy
        x0, x1, y0, y1 = ex - 27 * k, ex + 27 * k, cy - 39 * k, cy + 39 * k
        d.ellipse(P(x0, y0, x1, y1), fill=(58, 30, 46))
        d.ellipse(P(ex - 20 * k, y1 - 28 * k, ex + 20 * k, y1 - 2), fill=(108, 56, 70))
        hx = 4 if expr == "shy" else 0
        d.ellipse(P(ex - 17 + hx, y0 + 10, ex + 4 + hx, y0 + 36 * k), fill=(255, 255, 255))
        d.ellipse(P(ex + 6 + hx, y1 - 28 * k, ex + 17 + hx, y1 - 16 * k), fill=(255, 255, 255))
        d.arc(P(ex - 31 * k, y0 - 6, ex + 31 * k, y0 + 66 * k), 195, 345, fill=(52, 28, 40), width=int(7 * S))
        if name == "Marinette":
            sd = -1 if ex < 280 else 1
            d.line(P(ex + sd * 28 * k, cy - 13, ex + sd * 44 * k, cy - 27), fill=(52, 28, 40), width=int(5 * S))
    lift, inner, arch = 0, 0, 0
    if expr in ("sad", "worried"): inner = 16
    elif expr in ("surprised", "excited"): lift, arch = 18, 6
    elif expr == "embarrassed": inner = 9
    if expr == "confused":
        _brow(cv, name, 214, -1, 14, 0, 2); _brow(cv, name, 346, 1, -4, 0, 0)
    else:
        _brow(cv, name, 214, -1, lift, inner, arch); _brow(cv, name, 346, 1, lift, inner, arch)
    if laugh:
        d.pieslice(P(244, 402, 316, 464), 0, 180, fill=MOUTH); d.pieslice(P(262, 434, 298, 464), 0, 180, fill=TONGUE)
    elif m > 0.06:
        w, h = 12 + 9 * m, 14 + 34 * m
        d.ellipse(P(280 - w, 412, 280 + w, 412 + h), fill=MOUTH)
        if m > 0.55: d.ellipse(P(280 - w * 0.6, 412 + h * 0.55, 280 + w * 0.6, 412 + h * 0.95), fill=TONGUE)
    elif expr == "happy": d.arc(P(248, 400, 312, 442), 15, 165, fill=INK, width=int(6 * S))
    elif expr == "excited":
        d.pieslice(P(250, 406, 310, 458), 0, 180, fill=MOUTH); d.pieslice(P(266, 432, 294, 458), 0, 180, fill=TONGUE)
    elif expr == "surprised": d.ellipse(P(266, 414, 294, 450), fill=MOUTH)
    elif expr == "sad": d.arc(P(260, 428, 300, 456), 200, 340, fill=INK, width=int(6 * S))
    elif expr in ("worried", "confused"): d.line(P(258, 436, 270, 428, 282, 438, 296, 428), fill=INK, width=int(5 * S))
    elif expr in ("embarrassed", "shy"): d.arc(P(266, 414, 294, 434), 20, 160, fill=INK, width=int(5 * S))
    else: d.arc(P(262, 410, 298, 436), 15, 165, fill=INK, width=int(5 * S))
    if expr in ("embarrassed", "worried"):
        cv.poly([(412, 236), (402, 262), (422, 262)], (169, 208, 245)); cv.ell((402, 254, 422, 274), (169, 208, 245))
    c = tuple(int(v * S) for v in CROP)
    im = cv.im.crop(c)
    return im.resize((int(im.width * SCALE / S), int(im.height * SCALE / S)), Image.LANCZOS)


def head(name, expr="neutral", mouth=0.0, blink=False, laugh=False):
    mq = 0 if mouth <= 0.06 else max(1, min(6, int(round(mouth * 6))))
    return _head(name, expr if expr in EXPRESSIONS else "neutral", mq, bool(blink), bool(laugh))
