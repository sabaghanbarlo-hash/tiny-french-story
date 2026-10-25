"""Marinette and Adrien: one rigged drawing each (fixed proportions, outfit, hair). Poses only change limbs, face and held item."""
import math
from PIL import Image, ImageDraw, ImageChops
from .config import CHARS
from . import items as IT

SW, SH, CX, FY = 840, 1000, 420, 920
HEAD_K = 1.22   # chibi head scale about the neck
K_HEAD = 0.63   # scale from the face design shared with the Small videos (560-wide canvas)


def _bez(p0, p1, p2, n=14):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in [i / n for i in range(n + 1)]]


def _lock(root, ctrl, tip, width, n=14):
    """Pointed hair lock along a curve: thick in the middle, sharp at the tip."""
    c = _bez(root, ctrl, tip, n); left, right = [], []
    for i, (x, y) in enumerate(c):
        a = c[min(i + 1, n)]; b = c[max(i - 1, 0)]
        dx, dy = a[0] - b[0], a[1] - b[1]; L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        w = 0 if i == n else width * math.sin(math.pi * (0.12 + 0.88 * i / n) ** 0.9) * (1 - 0.15 * i / n) / 2
        left.append((x + nx * w, y + ny * w)); right.append((x - nx * w, y - ny * w))
    return left + right[::-1]


def _mk(d, cx, hy):
    T = lambda p: (cx + (p[0] - 280) * K_HEAD, hy + (p[1] - 308) * K_HEAD)
    poly = lambda pts, col: d.polygon([T(p) for p in pts], fill=col)
    ell = lambda b, col: d.ellipse((*T((b[0], b[1])), *T((b[2], b[3]))), fill=col)
    line = lambda pts, col, w: d.line([T(p) for p in pts], fill=col, width=max(2, int(w * K_HEAD * 1.2)), joint="curve")
    return poly, ell, line

def _arm(d, sx, sy, hx, hy, col, skin, side, w=46):
    ex, ey = sx + (hx - sx) * 0.5 + side * 16, sy + (hy - sy) * 0.5 + 6
    d.line((sx, sy, ex, ey), fill=col, width=w); d.line((ex, ey, hx, hy), fill=col, width=w - 6)
    d.ellipse((sx - w // 2, sy - w // 2, sx + w // 2, sy + w // 2), fill=col); d.ellipse((ex - w // 2 + 3, ey - w // 2 + 3, ex + w // 2 - 3, ey + w // 2 - 3), fill=col)
    d.ellipse((hx - 25, hy - 25, hx + 25, hy + 25), fill=skin)

def _brow(d, x, y, tilt, col, w=8, ln=22):
    d.line((x - ln, y + tilt, x + ln, y - tilt), fill=col, width=w)

def _face(d, name, cx, hy, expr, mouth, act, t, fdx):
    c = CHARS[name]; ink = (58, 40, 36); iris = c["iris"]; hair = c.get("brow", c["hair"])
    ex = (cx + fdx - 36, cx + fdx + 36); ey = hy + 6
    blink = (int(t * 1000) % 3300) < 120
    closed = act == "laugh" or blink
    blush = expr in ("embarrassed", "shy", "happy", "excited")
    d.ellipse((cx + fdx - 70, hy + 34, cx + fdx - 46, hy + 48), fill=(250, 160, 168) if blush else (252, 190, 186))
    d.ellipse((cx + fdx + 46, hy + 34, cx + fdx + 70, hy + 48), fill=(250, 160, 168) if blush else (252, 190, 186))
    big = expr in ("surprised", "excited")
    for i, x in enumerate(ex):
        if closed or expr == "embarrassed":
            d.arc((x - 16, ey - 10, x + 16, ey + 16), 200, 340, fill=ink, width=6)
        elif expr == "happy":
            d.arc((x - 16, ey - 8, x + 16, ey + 18), 200, 340, fill=ink, width=6)
        else:
            rx, ry = (20, 29) if big else (17, 24)
            oy = 6 if expr in ("sad", "shy") else 0
            d.ellipse((x - rx, ey - ry + oy, x + rx, ey + ry + oy), fill=ink)
            d.ellipse((x - rx + 4, ey - ry + 4 + oy, x + rx - 4, ey + ry - 4 + oy), fill=iris)
            px = x + (6 if expr == "shy" else 0); py = ey + oy + (8 if expr in ("shy", "sad") else 0)
            d.ellipse((px - 6, py - 7, px + 6, py + 7), fill=ink)
            d.ellipse((x - rx + 7, ey - ry + 7 + oy, x - rx + 19, ey - ry + 19 + oy), fill=(255, 255, 255))
            if name == "Marinette": sg = -1 if i == 0 else 1; d.line((x + sg * (rx - 3), ey - 8 + oy, x + sg * (rx + 11), ey - 18 + oy), fill=ink, width=5)
            if expr == "excited": d.ellipse((x + 3, ey + 2 + oy, x + 9, ey + 8 + oy), fill=(255, 255, 255))
    by = ey - 38
    if expr in ("sad", "worried"):
        _brow(d, ex[0], by, -9, hair); _brow(d, ex[1], by, 9, hair)
    elif expr == "confused":
        _brow(d, ex[0], by - 8, 8, hair); _brow(d, ex[1], by + 6, -4, hair)
    elif expr in ("surprised", "excited"):
        _brow(d, ex[0], by - 14, 0, hair); _brow(d, ex[1], by - 14, 0, hair)
    elif expr == "embarrassed":
        _brow(d, ex[0], by, -7, hair); _brow(d, ex[1], by, 7, hair)
    else:
        _brow(d, ex[0], by, 2, hair); _brow(d, ex[1], by, -2, hair)
    mx, my = cx + fdx, hy + 62
    d.line((mx + 4, hy + 34, mx + 10, hy + 40), fill=(214, 150, 130), width=4)
    if act == "laugh":
        d.pieslice((mx - 30, my - 18, mx + 30, my + 34), 0, 180, fill=(150, 60, 70)); d.pieslice((mx - 16, my + 6, mx + 16, my + 34), 0, 180, fill=(240, 130, 140)); return
    if mouth > 0.06:
        h = 8 + int(34 * mouth); wdt = 18 + int(8 * mouth)
        d.ellipse((mx - wdt, my - 4, mx + wdt, my - 4 + h), fill=(150, 60, 70)); return
    if expr == "happy": d.arc((mx - 28, my - 22, mx + 28, my + 16), 15, 165, fill=(150, 60, 70), width=6)
    elif expr == "excited": d.pieslice((mx - 28, my - 18, mx + 28, my + 30), 0, 180, fill=(150, 60, 70)); d.pieslice((mx - 14, my + 4, mx + 14, my + 30), 0, 180, fill=(240, 130, 140))
    elif expr == "surprised": d.ellipse((mx - 13, my - 2, mx + 13, my + 30), fill=(150, 60, 70))
    elif expr == "sad": d.arc((mx - 22, my + 4, mx + 22, my + 34), 200, 340, fill=(150, 60, 70), width=6)
    elif expr == "worried": d.line((mx - 18, my + 14, mx - 6, my + 8, mx + 6, my + 14, mx + 18, my + 8), fill=(150, 60, 70), width=5)
    elif expr == "confused": d.line((mx - 18, my + 12, mx - 6, my + 6, mx + 4, my + 14, mx + 18, my + 6), fill=(150, 60, 70), width=5)
    elif expr in ("embarrassed", "shy"): d.arc((mx - 14, my - 6, mx + 14, my + 14), 20, 160, fill=(150, 60, 70), width=5)
    else: d.arc((mx - 18, my - 12, mx + 18, my + 12), 20, 160, fill=(150, 60, 70), width=5)
    if expr in ("embarrassed", "worried"):
        sx = cx + fdx + 84; d.polygon([(sx, hy - 28), (sx - 10, hy - 4), (sx + 10, hy - 4)], fill=(169, 208, 245)); d.ellipse((sx - 10, hy - 8, sx + 10, hy + 8), fill=(169, 208, 245))

def draw(name, P):
    """P: face(+1/-1), expr, walking(0..1), phase, act, ap, item, bites, mouth, t -> RGBA sprite (feet at FY, centre CX)."""
    c = CHARS[name]; img = Image.new("RGBA", (SW, SH), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    act, ap, t = P["act"], P["ap"], P["t"]; expr = P["expr"]; walk = P["walking"]; ph = P["phase"]
    dy = 0.0; hdy = 0.0; lean = 0
    if walk: dy -= 9 * abs(math.sin(ph))
    if act == "jump": dy -= 150 * math.sin(math.pi * ap)
    elif act == "hop": dy -= 46 * math.sin(math.pi * ap)
    elif act == "cheer": dy -= 46 * abs(math.sin(2 * math.pi * ap * 2))
    elif act == "laugh": dy -= 8 * abs(math.sin(ap * 30))
    elif act == "bend": lean = int(60 * math.sin(math.pi * ap))
    if act == "nod": hdy = 16 * math.sin(2 * math.pi * ap * 2)
    if P["mouth"] > 0.1: hdy += 3 * math.sin(t * 22)
    y = int(FY + dy); cx = CX
    d.ellipse((cx - 120, FY - 14, cx + 120, FY + 22), fill=(0, 0, 0, 46))
    hy = y - 484 + int(hdy) + lean // 2
    s = math.sin(ph) * walk
    jacket, skin, trouser, top = c["jacket"], c["skin"], c["trouser"], c["top"]
    fdx = 11
    for i, side in enumerate((-1, 1)):
        sw = s * 48 * (1 if side > 0 else -1); lift = max(0, math.sin(ph + (0 if side > 0 else math.pi))) * 22 * walk
        hx, hyp = cx + side * 34, y - 176; fx, fyp = cx + side * 34 + sw, y - 14 - lift
        d.line((hx, hyp, fx, fyp), fill=trouser, width=58); d.ellipse((hx - 29, hyp - 29, hx + 29, hyp + 29), fill=trouser)
        d.rounded_rectangle((fx - 38 + 6, fyp - 8, fx + 38 + 6, fyp + 26), radius=14, fill=c["shoe"])
    sx0 = cx - 106; sy0 = y - 384 + lean
    bx, by = sx0 - 14 - s * 6, sy0 + 178 + s * 22
    if act == "cheer": bx, by = sx0 - 60, sy0 - 150 + 22 * math.sin(ap * 40)
    if act == "jump": bx, by = sx0 - 70, sy0 - 40
    _arm(d, sx0, sy0, bx, by, jacket, skin, -1)
    d.rounded_rectangle((cx - 108, y - 408 + lean, cx + 108, y - 160), radius=92, fill=jacket, corners=(True, True, False, False))
    d.rounded_rectangle((cx - 108, y - 300, cx + 108, y - 160), radius=34, fill=jacket, corners=(False, False, True, True))
    pw = 64 if name == "Adrien" else 54
    d.polygon([(cx - pw, y - 408 + lean), (cx + pw, y - 408 + lean), (cx + pw - 6, y - 162), (cx - pw + 6, y - 162)], fill=top)
    if name == "Adrien":   # black tee with rainbow stripes, V neck
        for k, col in enumerate(((110, 176, 120), (150, 108, 190), (244, 202, 100))):
            yy = y - 290 + k * 28; d.polygon([(cx - pw + 4, yy), (cx + pw - 4, yy), (cx + pw - 5, yy + 18), (cx - pw + 5, yy + 18)], fill=col)
        d.polygon([(cx - 34, y - 408 + lean), (cx + 34, y - 408 + lean), (cx, y - 336 + lean)], fill=skin)
    else:                  # white floral top, scoop neck
        d.polygon([(cx - 28, y - 408 + lean), (cx + 28, y - 408 + lean), (cx, y - 350 + lean)], fill=skin)
        for fx, fy in ((cx - 14, y - 282), (cx + 14, y - 258), (cx - 4, y - 226)):
            d.ellipse((fx - 10, fy - 10, fx + 10, fy + 10), fill=(238, 150, 170)); d.ellipse((fx - 3, fy - 3, fx + 3, fy + 3), fill=(252, 220, 120))
    d.line((cx - pw, y - 408 + lean, cx - pw + 6, y - 162), fill=c["edge"], width=5); d.line((cx + pw, y - 408 + lean, cx + pw - 6, y - 162), fill=c["edge"], width=5)
    d.line((cx - 90, y - 396 + lean, cx + 96, y - 190), fill=c["strap"], width=16)
    if name == "Marinette":
        d.rounded_rectangle((cx + 62, y - 250, cx + 160, y - 160), radius=14, fill=c["bag"], outline=c["strap"], width=4); d.polygon([(cx + 112, y - 222), (cx + 120, y - 206), (cx + 138, y - 204), (cx + 124, y - 194), (cx + 128, y - 178), (cx + 112, y - 188), (cx + 96, y - 178), (cx + 100, y - 194), (cx + 86, y - 204), (cx + 104, y - 206)], fill=(255, 214, 120))
    else:
        d.rounded_rectangle((cx + 62, y - 262, cx + 156, y - 170), radius=12, fill=c["bag"], outline=c["strap"], width=4); d.rectangle((cx + 62, y - 262, cx + 156, y - 236), fill=c["strap"])
    body_d = d
    hd = Image.new("RGBA", (SW, SH), (0, 0, 0, 0)); d = ImageDraw.Draw(hd)
    poly, ell, line = _mk(d, cx, hy)
    if name == "Adrien":   # swept blond hair, a boy's cut
        g, gd, gl = c["hair"], c["hair_d"], c["hl"]
        ell((112, 112, 448, 440), g)
        for pts in (_lock((150, 250), (100, 300), (74, 372), 70), _lock((410, 250), (462, 290), (486, 352), 64), _lock((262, 124), (288, 76), (338, 58), 54)):
            poly(pts, g)
        d.ellipse((cx - 92, hy - 94, cx + 92, hy + 94), fill=skin)
        poly([(118, 262), (124, 190), (196, 126), (330, 116), (432, 184), (442, 262), (430, 226), (300, 214), (180, 226)], g)
        for root, ctrl, tip, wd in (((400, 150), (420, 215), (392, 262), 66), ((340, 140), (330, 225), (296, 276), 70), ((276, 132), (240, 215), (206, 282), 76),
                                    ((206, 140), (166, 220), (150, 310), 74), ((140, 190), (118, 240), (124, 300), 50)):
            poly(_lock(root, ctrl, tip, wd), g)
        for root, ctrl, tip in (((390, 150), (360, 200), (330, 232)), ((300, 140), (250, 190), (214, 236)), ((236, 132), (196, 180), (168, 232)), ((330, 120), (400, 150), (428, 214))):
            line(_bez(root, ctrl, tip, 10), gd, 6)
        for root, ctrl, tip in (((340, 130), (300, 150), (268, 178)), ((240, 126), (212, 146), (196, 176))):
            line(_bez(root, ctrl, tip, 8), gl, 5)
    else:                  # navy hair with bangs, two low pigtails with small red ties
        n, nl = c["hair"], c["hl"]
        ell((106, 106, 454, 440), n); poly(_lock((130, 250), (112, 360), (140, 470), 80), n); poly(_lock((430, 250), (448, 360), (420, 470), 80), n)
        d.ellipse((cx - 92, hy - 94, cx + 92, hy + 94), fill=skin)
        poly([(112, 270), (118, 196), (196, 124), (330, 114), (436, 186), (448, 270), (430, 250), (300, 240), (170, 255)], n)
        for root, ctrl, tip, wd in (((178, 134), (140, 240), (180, 346), 84), ((262, 126), (220, 210), (222, 300), 84), ((330, 126), (372, 200), (338, 292), 84), ((404, 140), (434, 220), (404, 300), 60)):
            poly(_lock(root, ctrl, tip, wd), n)
        ell((80, 470, 206, 650), n); ell((354, 470, 480, 650), n)
        poly(_lock((160, 440), (150, 470), (136, 520), 54), n); poly(_lock((400, 440), (410, 470), (424, 520), 54), n)
        ell((146, 456, 170, 486), c["ribbon"]); ell((390, 456, 414, 486), c["ribbon"])
        for root, ctrl, tip in (((170, 140), (130, 220), (168, 320)), ((260, 130), (222, 180), (232, 250)), ((406, 150), (432, 220), (404, 290))):
            line(_bez(root, ctrl, tip, 10), nl, 6)
    _face(d, name, cx, hy, expr, P["mouth"], act, t, fdx)
    ax, ay = cx, hy + 92
    hd = hd.resize((int(SW * HEAD_K), int(SH * HEAD_K)), Image.LANCZOS)
    img.paste(hd, (int(ax - ax * HEAD_K), int(ay - ay * HEAD_K)), hd)
    d = body_d
    sx1 = cx + 106; sy1 = y - 384 + lean; item = P["item"]
    hx, hyy = sx1 + 14 + s * 6, sy1 + 178 - s * 22
    mouth_pt = (cx + int((fdx + 34) * HEAD_K), hy + 92 + int((66 - 92) * HEAD_K))
    if item and act not in ("eat", "drink", "give", "wave", "cheer", "jump"): hx, hyy = sx1 + 70, sy1 + 112
    if act == "wave": hx, hyy = sx1 + 70 + 26 * math.sin(ap * 2 * math.pi * 3), sy1 - 170
    elif act == "cheer": hx, hyy = sx1 + 62, sy1 - 150 + 22 * math.sin(ap * 40)
    elif act == "jump": hx, hyy = sx1 + 70, sy1 - 40
    elif act == "give": u = math.sin(math.pi * min(1.0, ap)); hx, hyy = sx1 + 40 + 150 * u, sy1 + 80
    elif act in ("eat", "drink"):
        q = (ap * (3 if act == "eat" else 1.2)) % 1.0; u = math.sin(math.pi * q)
        hx, hyy = sx1 + 70 + (mouth_pt[0] - sx1 - 70) * u, sy1 + 112 + (mouth_pt[1] - sy1 - 112) * u
    elif act == "bend": hx, hyy = sx1 + 90, sy1 + 170 + 70 * math.sin(math.pi * ap)
    _arm(d, sx1, sy1, hx, hyy, jacket, skin, 1)
    if item:
        IT.draw(d, item, int(hx + 28), int(hyy - 34), P["bites"])
        d.ellipse((hx - 25, hyy - 25, hx + 25, hyy + 25), fill=skin)
    if P["face"] < 0: img = img.transpose(Image.FLIP_LEFT_RIGHT)
    return img
