"""Camille and Julien: one rigged drawing each (fixed proportions, outfit, hair). Poses only change limbs, face and held item."""
import math
from PIL import Image, ImageDraw, ImageChops
from .config import CHARS
from . import items as IT

SW, SH, CX, FY = 840, 1000, 420, 920
HEAD_K = 1.22   # chibi head scale about the neck

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
    d.ellipse((cx + fdx - 76, hy + 30, cx + fdx - 42, hy + 50), fill=(250, 160, 168) if blush else (252, 190, 186))
    d.ellipse((cx + fdx + 42, hy + 30, cx + fdx + 76, hy + 50), fill=(250, 160, 168) if blush else (252, 190, 186))
    big = expr in ("surprised", "excited")
    for i, x in enumerate(ex):
        if closed or expr == "embarrassed":
            d.arc((x - 16, ey - 10, x + 16, ey + 16), 200, 340, fill=ink, width=6)
        elif expr == "happy":
            d.arc((x - 16, ey - 8, x + 16, ey + 18), 200, 340, fill=ink, width=6)
        else:
            rx, ry = (17, 25) if big else (14, 20)
            oy = 6 if expr in ("sad", "shy") else 0
            d.ellipse((x - rx, ey - ry + oy, x + rx, ey + ry + oy), fill=ink)
            d.ellipse((x - rx + 4, ey - ry + 4 + oy, x + rx - 4, ey + ry - 4 + oy), fill=iris)
            px = x + (6 if expr == "shy" else 0); py = ey + oy + (8 if expr in ("shy", "sad") else 0)
            d.ellipse((px - 6, py - 7, px + 6, py + 7), fill=ink)
            d.ellipse((x - rx + 8, ey - ry + 8 + oy, x - rx + 17, ey - ry + 17 + oy), fill=(255, 255, 255))
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
    d.rounded_rectangle((cx - 108, y - 408 + lean, cx + 108, y - 160), radius=62, fill=jacket)
    if name == "Julien":   # breton stripes, clipped to the torso
        m = Image.new("L", (SW, SH), 0); ImageDraw.Draw(m).rounded_rectangle((cx - 108, y - 408 + lean, cx + 108, y - 160), radius=62, fill=255)
        st = Image.new("RGBA", (SW, SH), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
        for yy in range(int(y - 400 + lean), int(y - 160), 46): sd.rectangle((cx - 110, yy, cx + 110, yy + 17), fill=c["top"] + (255,))
        img.paste(st, (0, 0), ImageChops.multiply(st.getchannel("A"), m))
    d.polygon([(cx - 44, y - 408 + lean), (cx + 44, y - 408 + lean), (cx + 6, y - 300), (cx - 6, y - 300)], fill=top); d.rectangle((cx - 6, y - 300, cx + 6, y - 162), fill=top)
    d.line((cx - 44, y - 408 + lean, cx - 6, y - 300), fill=c["edge"], width=6); d.line((cx + 44, y - 408 + lean, cx + 6, y - 300), fill=c["edge"], width=6)
    d.line((cx - 90, y - 396 + lean, cx + 96, y - 190), fill=c["strap"], width=16)
    if name == "Camille":
        d.rounded_rectangle((cx + 62, y - 250, cx + 160, y - 160), radius=14, fill=c["bag"], outline=c["strap"], width=4); d.polygon([(cx + 112, y - 222), (cx + 120, y - 206), (cx + 138, y - 204), (cx + 124, y - 194), (cx + 128, y - 178), (cx + 112, y - 188), (cx + 96, y - 178), (cx + 100, y - 194), (cx + 86, y - 204), (cx + 104, y - 206)], fill=(255, 214, 120))
    else:
        d.rounded_rectangle((cx + 62, y - 262, cx + 156, y - 170), radius=12, fill=c["bag"], outline=c["strap"], width=4); d.rectangle((cx + 62, y - 262, cx + 156, y - 236), fill=c["strap"])
    if name == "Julien":   # red neckerchief, under the head
        d.polygon([(cx - 52, y - 410 + lean), (cx + 52, y - 410 + lean), (cx + 4, y - 322 + lean)], fill=c["scarf"])
        d.ellipse((cx - 14, y - 346 + lean, cx + 14, y - 318 + lean), fill=c["edge"])
    body_d = d
    hd = Image.new("RGBA", (SW, SH), (0, 0, 0, 0)); d = ImageDraw.Draw(hd)
    if name == "Camille":   # high bun behind the head
        d.ellipse((cx - 52, hy - 176, cx + 48, hy - 80), fill=c["hair"]); d.arc((cx - 40, hy - 166, cx + 30, hy - 104), 200, 300, fill=c["hl"], width=6)
    d.ellipse((cx - 92, hy - 94, cx + 92, hy + 94), fill=skin)
    if name == "Camille":
        d.rounded_rectangle((cx - 106, hy - 30, cx - 76, hy + 78), radius=18, fill=c["hair"]); d.rounded_rectangle((cx + 76, hy - 30, cx + 106, hy + 78), radius=18, fill=c["hair"])
        d.pieslice((cx - 104, hy - 118, cx + 104, hy + 70), 180, 360, fill=c["hair"])
        d.polygon([(cx - 100, hy - 6), (cx - 30, hy - 96), (cx + 20, hy - 70), (cx + 60, hy - 100), (cx + 100, hy - 6), (cx + 70, hy - 40), (cx + 20, hy - 30), (cx - 40, hy - 36)], fill=c["hair"])
        d.line((cx - 20, hy - 100, cx - 44, hy - 40), fill=c["hl"], width=7); d.line((cx + 30, hy - 96, cx + 10, hy - 44), fill=c["hl"], width=7)
        rx, ry = cx - 2, hy - 104   # ribbon at the base of the bun
        d.polygon([(rx, ry), (rx - 46, ry - 26), (rx - 46, ry + 24)], fill=c["ribbon"]); d.polygon([(rx, ry), (rx + 46, ry - 26), (rx + 46, ry + 24)], fill=c["ribbon"])
        d.ellipse((rx - 12, ry - 12, rx + 12, ry + 12), fill=(176, 44, 66))
    else:
        d.pieslice((cx - 104, hy - 124, cx + 104, hy + 60), 180, 360, fill=c["hair"])
        d.polygon([(cx - 100, hy - 14), (cx - 74, hy - 74), (cx - 46, hy - 24), (cx - 18, hy - 84), (cx + 8, hy - 30), (cx + 40, hy - 80), (cx + 62, hy - 26), (cx + 98, hy - 66), (cx + 102, hy - 8), (cx + 60, hy - 40), (cx - 10, hy - 36)], fill=c["hair"])
        d.polygon([(cx + 88, hy - 40), (cx + 112, hy - 70), (cx + 108, hy - 24)], fill=c["hair"])
        d.polygon([(cx - 70, hy - 104), (cx - 10, hy - 150), (cx + 56, hy - 124), (cx + 14, hy - 96)], fill=c["hair"])   # side-swept wave
        d.polygon([(cx + 4, hy - 112), (cx + 26, hy - 162), (cx + 38, hy - 108)], fill=c["hair"])                       # cowlick
        d.line((cx - 50, hy - 104, cx - 6, hy - 136), fill=c["hl"], width=7); d.line((cx - 60, hy - 60, cx - 44, hy - 28), fill=c["hl"], width=6)
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
