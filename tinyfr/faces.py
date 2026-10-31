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
        "Marinette": dict(main=(50, 68, 122), dark=(34, 46, 92), light=(92, 112, 170), brow=(34, 46, 92), tie=(206, 54, 64)),
        "Alia": dict(main=(145, 62, 48), dark=(105, 42, 38), light=(205, 112, 78), brow=(105, 42, 38), tie=(205, 153, 54)),
        "Nino": dict(main=(82, 53, 39), dark=(58, 38, 31), light=(133, 91, 65), brow=(58, 38, 31), iris=(75, 142, 105)),
        "Chloé": dict(main=(151, 105, 67), dark=(111, 74, 48), light=(207, 161, 111), brow=(111, 74, 48), tie=(181, 157, 224)),
        "Lucas": dict(main=(35, 31, 34), dark=(20, 18, 21), light=(83, 73, 75), brow=(20, 18, 21)),
        "Cat": dict(main=(247, 190, 82), dark=(220, 151, 55), light=(255, 218, 135), brow=(220, 151, 55), iris=(112, 132, 82)),
        "Bugaboo": dict(main=(48, 61, 112), dark=(34, 44, 92), light=(76, 91, 145), brow=(34, 44, 92), tie=(225, 45, 52), iris=(105, 75, 78))}
MASK = [(145, 325), (170, 290), (220, 300), (280, 325), (340, 300), (390, 290), (415, 325), (390, 385), (345, 390), (280, 370), (215, 390), (170, 385)]
MASK_COLOR = {"Cat": (35, 31, 39), "Bugaboo": (224, 45, 52)}
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
    """Hair, ears, face and fringe: everything that does not move. Every character has their own hairstyle."""
    cv = _Canvas(); h = HAIR[name]; g = h["main"]
    mx = (lambda pts: [(560 - x, y) for x, y in pts]) if name == "Nino" else (lambda pts: pts)     # Nino's fringe sweeps the other way
    def mlock(root, ctrl, tip, wd, n=14): return mx(_lock(root, ctrl, tip, wd, n))
    def mbez(a, b, c, n=10): return mx(_bez(a, b, c, n))
    if name in ("Adrien", "Nino", "Lucas", "Cat"):
        if name == "Lucas":                       # soft short curtain cut with a little tuft
            def back(dd):
                cv.ell((112, 106, 448, 442), g, dd)
                for pts in (_lock((130, 250), (112, 320), (140, 392), 70), _lock((430, 250), (448, 320), (420, 392), 70), _lock((272, 124), (288, 74), (338, 60), 52)): cv.poly(pts, g, dd)
        else:
            def back(dd):
                cv.ell((112, 112, 448, 440), g, dd)
                for pts in (mlock((150, 250), (100, 300), (74, 372), 70), mlock((410, 250), (462, 290), (486, 352), 64), mlock((262, 124), (288, 76), (338, 58), 54)): cv.poly(pts, g, dd)
        cv.layer(back, g, 4)
        cv.ell((130, 316, 180, 396), SKIN); cv.ell((136, 154, 424, 462), SKIN)
        if name in MASK_COLOR: cv.poly(MASK, MASK_COLOR[name])      # Cat's eye mask sits under the fringe
        if name == "Lucas":
            def front(dd):
                cv.poly([(112, 270), (118, 196), (196, 124), (330, 114), (436, 186), (448, 270), (430, 250), (300, 240), (170, 255)], g, dd)
                for root, ctrl, tip, wd in (((190, 134), (150, 215), (170, 292), 80), ((262, 126), (232, 200), (236, 266), 80), ((330, 126), (352, 200), (330, 268), 80), ((404, 140), (434, 210), (414, 278), 62)):
                    cv.poly(_lock(root, ctrl, tip, wd), g, dd)
            cv.layer(front, g, 2)
            for root, ctrl, tip in (((176, 140), (140, 214), (166, 280)), ((330, 130), (360, 190), (340, 250)), ((406, 150), (432, 214), (414, 268))):
                cv.line(_bez(root, ctrl, tip, 10), h["light"], 5)
            cv.ell((410, 384, 428, 404), (232, 188, 110))           # tiny gold earring
        else:
            def front(dd):
                cv.poly(mx([(118, 262), (124, 190), (196, 126), (330, 116), (432, 184), (442, 262), (430, 226), (300, 214), (180, 226)]), g, dd)
                for root, ctrl, tip, wd in (((400, 150), (420, 215), (392, 262), 66), ((340, 140), (330, 225), (296, 276), 70), ((276, 132), (240, 215), (206, 282), 76),
                                            ((206, 140), (166, 220), (150, 310), 74), ((140, 190), (118, 240), (124, 300), 50)):
                    cv.poly(mlock(root, ctrl, tip, wd), g, dd)
            cv.layer(front, g, 2)
            for root, ctrl, tip in (((390, 150), (360, 200), (330, 232)), ((300, 140), (250, 190), (214, 236)), ((236, 132), (196, 180), (168, 232)), ((330, 120), (400, 150), (428, 214))):
                cv.line(mbez(root, ctrl, tip), h["dark"], 6)
            for root, ctrl, tip in (((340, 130), (300, 150), (268, 178)), ((240, 126), (212, 146), (196, 176))):
                cv.line(mbez(root, ctrl, tip, 8), h["light"], 5)
        if name == "Cat":                                              # black cat ears with charcoal inner ears
            def ears(dd):
                cv.poly([(132, 190), (150, 62), (250, 174), (268, 204), (176, 214)], (22, 21, 27), dd); cv.poly([(332, 204), (350, 174), (444, 58), (456, 190), (408, 218)], (22, 21, 27), dd)
            cv.layer(ears, (22, 21, 27), 5)
            def inner(dd):
                cv.poly([(164, 178), (172, 100), (228, 174)], (75, 72, 82), dd); cv.poly([(372, 178), (436, 100), (430, 184)], (75, 72, 82), dd)
            cv.layer(inner, (75, 72, 82), 3)
        if name == "Nino":                                               # soft over-ear headphones
            cv.d.arc(cv.P(104, 132, 456, 470), 196, 344, fill=(48, 52, 60), width=int(14 * S))
            for c0 in (112, 448):
                cv.ell((c0 - 36, 288, c0 + 36, 392), (48, 52, 60)); cv.ell((c0 - 22, 304, c0 + 22, 376), (112, 124, 132)); cv.ell((c0 - 10, 322, c0 + 10, 358), (170, 184, 190))
    else:
        pig = name in ("Marinette", "Bugaboo")
        def back(dd):
            cv.ell((106, 106, 454, 440), g, dd)
            if name == "Alia":                 # soft bob that curls under
                cv.poly(_lock((136, 250), (100, 360), (158, 452), 92), g, dd); cv.poly(_lock((424, 250), (460, 360), (402, 452), 92), g, dd)
                cv.ell((112, 410, 176, 486), g, dd); cv.ell((384, 410, 448, 486), g, dd)
            elif name == "Chloé":                 # long hair falling past the shoulders
                cv.poly(_lock((128, 250), (104, 430), (136, 590), 104), g, dd); cv.poly(_lock((432, 250), (456, 430), (424, 590), 104), g, dd)
            else:
                cv.poly(_lock((130, 250), (112, 360), (140, 470), 80), g, dd); cv.poly(_lock((430, 250), (448, 360), (420, 470), 80), g, dd)
        cv.layer(back, g, 6 if name != "Marinette" else 5)
        cv.ell((136, 154, 424, 462), SKIN)
        if name in MASK_COLOR: cv.poly(MASK, MASK_COLOR[name])      # Bugaboo's red mask
        locks_ = (((180, 136), (158, 226), (226, 294), 82), ((262, 126), (250, 212), (316, 280), 84), ((336, 128), (374, 196), (400, 252), 76), ((408, 142), (440, 214), (432, 284), 58)) if name == "Chloé" else \
                 (((178, 134), (140, 240), (180, 346), 84), ((262, 126), (220, 210), (222, 300), 84), ((330, 126), (372, 200), (338, 292), 84), ((404, 140), (434, 220), (404, 300), 60))
        def front(dd):
            cv.poly([(112, 270), (118, 196), (196, 124), (330, 114), (436, 186), (448, 270), (430, 250), (300, 240), (170, 255)], g, dd)
            for root, ctrl, tip, wd in locks_: cv.poly(_lock(root, ctrl, tip, wd), g, dd)
        cv.layer(front, g, 2)
        if pig:
            def tails(dd):
                cv.ell((80, 470, 206, 650), g, dd); cv.ell((354, 470, 480, 650), g, dd)
                cv.poly(_lock((160, 440), (150, 470), (136, 520), 54), g, dd); cv.poly(_lock((400, 440), (410, 470), (424, 520), 54), g, dd)
            cv.layer(tails, g, 6)
            cv.ell((146, 456, 170, 486), h["tie"]); cv.ell((390, 456, 414, 486), h["tie"])
            if name == "Bugaboo":                                            # red bows at the pigtail roots
                for bow in ([(151, 466), (112, 444), (120, 490), (151, 480)], [(165, 466), (202, 444), (194, 490), (165, 480)],
                            [(395, 466), (358, 444), (366, 490), (395, 480)], [(409, 466), (448, 444), (440, 490), (409, 480)]):
                    cv.poly(bow, h["tie"]); cv.line(bow + [bow[0]], (150, 28, 39), 2)
        for root, ctrl, tip in (((170, 140), (130, 220), (168, 320)), ((260, 130), (222, 180), (232, 250)), ((406, 150), (432, 220), (404, 290))):
            cv.line(_bez(root, ctrl, tip, 10), h["light"], 6)
        if pig:
            cv.line(_bez((110, 520), (100, 570), (130, 620), 10), h["light"], 5); cv.line(_bez((450, 520), (460, 570), (430, 620), 10), h["light"], 5)
        if name == "Chloé":
            cv.layer(lambda dd: (cv.poly(_lock((146, 300), (116, 440), (146, 570), 66), g, dd), cv.poly(_lock((414, 300), (444, 440), (414, 570), 66), g, dd)), g, 5)
            cv.line(_bez((132, 410), (120, 480), (140, 550), 10), h["light"], 5); cv.line(_bez((428, 410), (440, 480), (420, 550), 10), h["light"], 5)
            bow = (244, 150, 180)                                        # bow hair clip
            cv.poly([(176, 196), (146, 176), (146, 216)], bow); cv.poly([(176, 196), (206, 176), (206, 216)], bow); cv.ell((167, 187, 185, 205), (232, 120, 156))
        if name == "Alia":                                            # little flower clip
            for k in range(5):
                a = k * 1.2566 - 1.57; ex, ey = 404 + 17 * math.cos(a), 206 + 17 * math.sin(a)
                cv.ell((ex - 11, ey - 11, ex + 11, ey + 11), (255, 190, 206))
            cv.ell((396, 198, 412, 214), (255, 232, 140))
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
        d.ellipse(P(ex - 20 * k, y1 - 28 * k, ex + 20 * k, y1 - 2), fill=HAIR[name].get("iris", (108, 56, 70)))
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
    if name == "Alia":
        # Thin rounded glasses, positioned around both eyes.
        for ex in (214, 346):
            d.ellipse(P(ex - 38, 322, ex + 38, 394), outline=(120, 70, 52), width=int(5 * S))
        d.line(P(253, 356, 307, 356), fill=(105, 66, 52), width=int(5 * S))
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
