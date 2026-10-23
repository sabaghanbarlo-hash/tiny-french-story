"""More Paris scenes, built from small reusable components (shelves, counters, tables, signs, balustrade...).
Registered into scenes.SCENES. Rules: every prop sits at or behind the floor line (FLOOR), so characters walk in front of
furniture and never through it; spots are walkable x positions at least MIN_GAP apart; nothing important sits in the top
safe-area band (y < 220) or in the card band at the bottom."""
import math, random
from PIL import ImageDraw
from .config import *
from .fonts import font
from .scenes import FLOOR, HORIZON, lerp, grad, win, awning, clouds, tree, lamp, checker

def _make(name, fn, spots, aliases=()):
    return dict(name=name, draw=fn, spots=spots, aliases=list(aliases))

# ---------- reusable components ----------
def floor_band(d, top, bot, edge=None):
    grad(d, HORIZON, H, top, bot)
    if edge: d.rectangle((0, HORIZON, W, HORIZON + 14), fill=edge)

SIGN_MIN_Y = 400   # the renderer overlays the wordmark (y~230-306) and place pill (y~330-392); keep scene lettering below them

def sign(d, cx, cy, w, h, text, fill, fg=(255, 255, 255), size=46):
    if cy - h // 2 < SIGN_MIN_Y: raise ValueError(f"sign {text!r} at y={cy - h // 2} collides with the overlay band (needs y >= {SIGN_MIN_Y})")
    d.rounded_rectangle((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2), radius=h // 3, fill=fill)
    d.text((cx, cy), text, font=font(size), fill=fg, anchor="mm")

def shelf(d, x0, y0, x1, y1, rows, pal, seed=1, frame=(150, 108, 76), mode="books"):
    """Shelving unit filled with books (mode='books') or boxed goods (mode='goods')."""
    d.rectangle((x0, y0, x1, y1), fill=frame); rng = random.Random(seed); rh = (y1 - y0) / rows
    for r in range(rows):
        top = int(y0 + r * rh + 8); base = int(y0 + (r + 1) * rh - 8)
        d.rectangle((x0 + 8, top, x1 - 8, base), fill=lerp(frame, (0, 0, 0), 0.35)); x = x0 + 12
        while x < x1 - 30:
            w = rng.randint(16, 30) if mode == "books" else rng.randint(36, 54); w = min(w, x1 - 12 - x)
            h = rng.randint(int(rh * 0.5), int(rh - 24)) if mode == "books" else int(rh * 0.52); col = rng.choice(pal)
            if mode == "books": d.rectangle((x, base - h, x + w, base), fill=col, outline=lerp(col, (0, 0, 0), 0.25))
            else:
                d.rounded_rectangle((x, base - h, x + w, base), radius=6, fill=col); d.rectangle((x + 4, base - h + 10, x + w - 4, base - h + 22), fill=(255, 255, 255))
            x += w + 3
        d.rectangle((x0 + 4, base, x1 - 4, base + 8), fill=frame)

def counter(d, x0, x1, ytop, body, top, h=HORIZON + 10):
    d.rectangle((x0, ytop, x1, h), fill=body); d.rectangle((x0 - 10, ytop - 20, x1 + 10, ytop + 6), fill=top)

def round_table(d, cx, ytop, w, cloth, leg=(110, 90, 80)):
    d.ellipse((cx - w // 2, ytop, cx + w // 2, ytop + 46), fill=cloth); d.rectangle((cx - 8, ytop + 30, cx + 8, FLOOR), fill=leg); d.ellipse((cx - 56, FLOOR - 14, cx + 56, FLOOR + 6), fill=leg)

def plate(d, cx, cy, r=22, rim=(255, 255, 255)):
    d.ellipse((cx - r, cy - r // 3, cx + r, cy + r // 3), fill=rim, outline=(200, 204, 214))
    d.ellipse((cx - r // 2, cy - r // 6, cx + r // 2, cy + r // 6), fill=(244, 232, 214))

def frame_art(d, x, y, w, h, seed, frame=(190, 150, 80), pal=((246, 182, 205), (169, 208, 245), (255, 220, 140), (184, 214, 193), (185, 167, 245))):
    """Original abstract painting in a gilt frame."""
    d.rectangle((x - 12, y - 12, x + w + 12, y + h + 12), fill=frame); rng = random.Random(seed); d.rectangle((x, y, x + w, y + h), fill=rng.choice(pal))
    for _ in range(5):
        a, b = rng.randint(x, x + w - 30), rng.randint(y, y + h - 30)
        d.ellipse((a, b, a + rng.randint(30, w // 2), b + rng.randint(30, h // 2)), fill=rng.choice(pal))

def balustrade(d, ytop, ybase, stone=(226, 218, 206), shade=(196, 188, 178)):
    d.rectangle((0, ytop, W, ytop + 26), fill=stone); d.rectangle((0, ybase - 24, W, ybase), fill=stone)
    for x in range(10, W, 54):
        d.rounded_rectangle((x, ytop + 26, x + 30, ybase - 24), radius=12, fill=stone, outline=shade)
    d.rectangle((0, ytop + 26, W, ytop + 30), fill=shade)

def eiffel_tower(d, cx, base, h, col, sky):
    """Large lattice-style Eiffel Tower silhouette with arch, platforms and braces."""
    w = h * 0.44
    d.polygon([(cx - w / 2, base), (cx - w * 0.16, base - h * 0.5), (cx - w * 0.05, base - h * 0.84), (cx, base - h), (cx + w * 0.05, base - h * 0.84), (cx + w * 0.16, base - h * 0.5), (cx + w / 2, base)], fill=col)
    d.polygon([(cx - w * 0.30, base), (cx - w * 0.22, base - h * 0.16), (cx + w * 0.22, base - h * 0.16), (cx + w * 0.30, base)], fill=sky)
    d.arc((cx - w * 0.30, base - h * 0.24, cx + w * 0.30, base - h * 0.08), 180, 360, fill=col, width=int(h * 0.02))
    for f, ww in ((0.5, 0.40), (0.74, 0.22)): d.rectangle((cx - w * ww / 2, base - h * f - h * 0.012, cx + w * ww / 2, base - h * f + h * 0.012), fill=lerp(col, (255, 255, 255), 0.25))
    lc = lerp(col, (255, 255, 255), 0.45)
    for f0, f1 in ((0.17, 0.5), (0.5, 0.74), (0.74, 0.9)):
        ww0 = w * (1 - 1.35 * f0) * 0.36; ww1 = w * (1 - 1.35 * f1) * 0.36
        d.line((cx - ww0, base - h * f0, cx + ww1, base - h * f1), fill=lc, width=3); d.line((cx + ww0, base - h * f0, cx - ww1, base - h * f1), fill=lc, width=3)

def conveyor(d, x0, x1, y, belt=(70, 76, 96)):
    d.rounded_rectangle((x0, y, x1, y + 26), radius=10, fill=belt)
    for x in range(int(x0) + 14, int(x1) - 10, 34): d.line((x, y + 6, x, y + 20), fill=lerp(belt, (255, 255, 255), 0.3), width=3)

def basket(d, cx, y, col=(246, 182, 205)):
    d.polygon([(cx - 48, y), (cx + 48, y), (cx + 38, y + 40), (cx - 38, y + 40)], fill=col); d.arc((cx - 40, y - 30, cx + 40, y + 20), 180, 360, fill=lerp(col, (0, 0, 0), 0.25), width=5)

def crate_produce(d, x0, x1, y, col, seed=1, r=15):
    d.rectangle((x0, y, x1, y + 60), fill=(176, 130, 92)); d.rectangle((x0, y, x1, y + 8), fill=(150, 108, 76)); rng = random.Random(seed)
    for xx in range(int(x0) + 14, int(x1) - 10, r + 5):
        for k in range(2): d.ellipse((xx, y - 12 - k * 10 + rng.randint(-3, 3), xx + r * 2 - 4, y + 14 - k * 10), fill=lerp(col, (255, 255, 255), 0.1 * k))

# ---------- scenes ----------
def supermarket(img):
    d = ImageDraw.Draw(img); grad(d, 0, HORIZON, (240, 250, 244), (222, 240, 232))
    for x in range(120, W, 300): d.rectangle((x, 230, x + 160, 244), fill=(255, 255, 255)); d.rectangle((x + 10, 244, x + 150, 252), fill=(255, 250, 220))
    sign(d, 540, 470, 620, 110, "SUPERMARCHÉ", (90, 160, 120), size=62)
    for x, pal in ((0, ((246, 182, 205), (255, 220, 140), (169, 208, 245), (200, 230, 190))), (360, ((255, 236, 170), (250, 150, 130), (185, 167, 245), (255, 255, 255)))):
        shelf(d, x + 20, 560, x + 340, 1000, 4, pal, seed=x + 3, frame=(206, 214, 220), mode="goods")
    d.rectangle((14, 540, 40, HORIZON), fill=(206, 214, 220))
    crate_produce(d, 60, 250, 1040, (230, 70, 60), 1); crate_produce(d, 270, 440, 1040, (250, 190, 60), 2); crate_produce(d, 460, 620, 1040, (110, 180, 90), 3)
    d.rectangle((30, 1100, 640, 1112), fill=(150, 108, 76))
    counter(d, 740, W, 1010, (226, 230, 240), (176, 184, 200)); conveyor(d, 760, 1060, 984); basket(d, 880, 940)
    d.rectangle((960, 840, 1050, 984), fill=(70, 76, 96)); d.rectangle((972, 856, 1038, 900), fill=(169, 208, 245)); d.text((1005, 924), "€", font=font(34), fill=(255, 255, 255), anchor="mm")
    floor_band(d, (236, 238, 244), (212, 214, 224), edge=(190, 196, 206)); checker(d, HORIZON + 14, H, (244, 246, 250), (222, 226, 236), 110)

def bookstore(img):
    d = ImageDraw.Draw(img); grad(d, 0, HORIZON, (252, 238, 220), (240, 218, 196))
    pal = ((176, 70, 80), (70, 110, 150), (90, 140, 110), (220, 170, 80), (130, 90, 150), (240, 230, 214))
    shelf(d, 20, 520, 420, 1090, 5, pal, seed=11, mode="books"); shelf(d, 440, 520, 700, 1090, 5, pal, seed=12, mode="books")
    sign(d, 400, 450, 420, 84, "LIBRAIRIE", (120, 76, 56), (255, 220, 140), size=52)
    win(d, 720, 560, 160, 300, glass=(206, 230, 250)); d.rectangle((728, 760, 872, 860), fill=(246, 214, 206))
    d.rounded_rectangle((740, 980, 920, 1130), radius=40, fill=(190, 90, 100)); d.rounded_rectangle((720, 1040, 760, 1170), radius=18, fill=(170, 74, 86)); d.rounded_rectangle((900, 1040, 940, 1170), radius=18, fill=(170, 74, 86))
    d.rectangle((760, 1130, 780, 1190), fill=(110, 80, 70)); d.rectangle((880, 1130, 900, 1190), fill=(110, 80, 70))
    lamp(d, 1010, 1180, 520)
    d.rounded_rectangle((950, 1080, 1060, 1100), radius=6, fill=(150, 108, 76)); d.rectangle((1000, 1100, 1012, 1190), fill=(110, 80, 70))
    for k, col in enumerate(((176, 70, 80), (70, 110, 150))): d.rectangle((964, 1060 - k * 14, 1044, 1078 - k * 14), fill=col)
    floor_band(d, (206, 160, 118), (180, 134, 98), edge=(150, 108, 76))
    for x in range(-60, W + 60, 140): d.line((x, HORIZON, x - 70, H), fill=(170, 124, 90), width=3)

def restaurant(img):
    d = ImageDraw.Draw(img); grad(d, 0, HORIZON, (252, 240, 226), (246, 226, 208))
    d.rectangle((0, 820, W, HORIZON), fill=(170, 70, 84)); d.rectangle((0, 800, W, 826), fill=(236, 214, 190))
    for x in range(0, W, 120): d.rounded_rectangle((x + 10, 850, x + 100, 1100), radius=10, outline=(196, 100, 112), width=4)
    d.rounded_rectangle((640, 500, 1020, 800), radius=40, fill=(150, 108, 76)); d.rounded_rectangle((660, 520, 1000, 780), radius=30, fill=(196, 226, 248)); d.line((830, 520, 830, 780), fill=(150, 108, 76), width=8)
    d.polygon([(640, 500), (720, 500), (700, 800), (640, 800)], fill=(250, 214, 220)); d.polygon([(1020, 500), (940, 500), (960, 800), (1020, 800)], fill=(250, 214, 220))
    eiffel_tower(d, 830, 780, 230, (170, 180, 214), (196, 226, 248))
    d.rounded_rectangle((60, 500, 520, 790), radius=14, fill=(176, 130, 92)); d.rounded_rectangle((76, 516, 504, 774), radius=8, fill=(50, 70, 64))
    d.text((290, 560), "MENU DU JOUR", font=font(42), fill=(255, 255, 255), anchor="mm")
    for k, tx in enumerate(("Soupe", "Poulet", "Salade", "Gâteau")): d.text((120, 610 + k * 38), tx, font=font(30, False), fill=(240, 240, 230), anchor="lm"); d.text((470, 610 + k * 38), "· · ·", font=font(26, False), fill=(240, 240, 230), anchor="rm")
    for x in (250, 640, 960): d.line((x, 0, x, 190), fill=(80, 70, 90), width=4); d.pieslice((x - 54, 170, x + 54, 280), 180, 360, fill=(246, 182, 205)); d.ellipse((x - 14, 236, x + 14, 262), fill=(255, 236, 170))
    sign(d, 540, 450, 400, 70, "RESTAURANT", (120, 76, 56), (255, 220, 140), size=46)
    counter(d, 830, W, 1000, (150, 108, 76), (196, 150, 110))
    for x in (870, 960): d.rounded_rectangle((x - 16, 940, x + 16, 980), radius=8, fill=(255, 255, 255), outline=(200, 204, 214))
    floor_band(d, (236, 212, 184), (210, 184, 156), edge=(176, 130, 92)); checker(d, HORIZON + 14, H, (250, 244, 236), (232, 206, 196), 110)
    for cx in (330, 640):
        round_table(d, cx, 1090, 250, (255, 255, 255)); plate(d, cx - 56, 1108); plate(d, cx + 56, 1108); d.rectangle((cx - 5, 1070, cx + 5, 1100), fill=(255, 250, 220)); d.ellipse((cx - 6, 1058, cx + 6, 1074), fill=(255, 190, 90))

def train_station(img):
    d = ImageDraw.Draw(img); grad(d, 0, HORIZON, (226, 238, 246), (244, 244, 244))
    for x in range(0, W + 120, 120): d.arc((x - 300, 120, x + 300, 700), 180, 360, fill=(150, 160, 176), width=6)
    d.rectangle((0, 120, W, 134), fill=(150, 160, 176)); d.polygon([(0, 134), (W, 134), (W, 250), (0, 250)], fill=(204, 226, 244))
    for x in range(0, W, 90): d.line((x, 134, x + 30, 250), fill=(150, 160, 176), width=4)
    d.ellipse((470, 300, 610, 440), fill=(255, 255, 255), outline=(60, 66, 84), width=8); d.line((540, 370, 540, 322), fill=(60, 66, 84), width=6); d.line((540, 370, 580, 388), fill=(60, 66, 84), width=6)
    d.rounded_rectangle((120, 470, 640, 800), radius=20, fill=(34, 40, 60)); d.text((380, 510), "DÉPARTS", font=font(46), fill=(255, 214, 90), anchor="mm")
    for k, (a, b, c) in enumerate((("08:15", "Lyon", "A"), ("08:42", "Nice", "C"), ("09:05", "Lille", "B"), ("09:30", "Nantes", "D"))):
        y = 576 + k * 52; d.text((160, y), a, font=font(32), fill=(255, 255, 255), anchor="lm"); d.text((300, y), b, font=font(32), fill=(210, 224, 240), anchor="lm"); d.text((590, y), c, font=font(32), fill=(255, 214, 90), anchor="rm")
    d.rectangle((700, 430, 1080, 1130), fill=(210, 218, 230)); d.rounded_rectangle((716, 560, 1080, 1010), radius=30, fill=(56, 96, 170)); d.rectangle((716, 790, 1080, 810), fill=(255, 255, 255)); d.rectangle((716, 830, 1080, 842), fill=(210, 60, 70))
    for x in (760, 900): d.rounded_rectangle((x, 600, x + 110, 740), radius=16, fill=(196, 226, 248))
    d.rounded_rectangle((716, 1010, 1080, 1060), radius=10, fill=(40, 46, 64))
    d.rounded_rectangle((60, 880, 360, 1030), radius=16, fill=(236, 240, 246), outline=(150, 160, 190), width=5); d.rectangle((90, 920, 330, 960), fill=(169, 208, 245)); d.text((210, 940), "BILLETS", font=font(30), fill=(38, 48, 74), anchor="mm")
    d.rounded_rectangle((200, 1090, 460, 1116), radius=8, fill=(150, 108, 76)); d.rounded_rectangle((200, 1040, 460, 1070), radius=8, fill=(176, 130, 92)); d.rectangle((220, 1116, 232, 1190), fill=(60, 66, 84)); d.rectangle((430, 1116, 442, 1190), fill=(60, 66, 84))
    floor_band(d, (196, 198, 212), (170, 172, 190), edge=(150, 154, 172)); d.rectangle((0, 1260, W, 1290), fill=(250, 214, 90))

def museum(img):
    d = ImageDraw.Draw(img); grad(d, 0, HORIZON, (250, 244, 236), (238, 230, 218))
    d.rectangle((0, 260, W, 280), fill=(214, 202, 186)); d.rectangle((0, 1070, W, HORIZON), fill=(206, 192, 176))
    sign(d, 540, 450, 400, 84, "MUSÉE", (60, 70, 100), (255, 236, 190), size=54)
    frame_art(d, 90, 560, 250, 250, 1); frame_art(d, 380, 540, 230, 290, 2, frame=(150, 108, 76)); frame_art(d, 830, 560, 190, 250, 3)
    for x in (215, 495, 925): d.polygon([(x - 50, 860), (x + 50, 860), (x + 30, 900), (x - 30, 900)], fill=(206, 190, 168)); d.rectangle((x - 40, 900, x + 40, 912), fill=(176, 160, 140))
    d.rectangle((630, 760, 800, 1130), fill=(226, 218, 206)); d.rectangle((616, 740, 814, 774), fill=(206, 196, 184))
    d.ellipse((676, 520, 756, 610), fill=(240, 236, 228)); d.rounded_rectangle((668, 600, 764, 740), radius=30, fill=(240, 236, 228)); d.polygon([(668, 640), (620, 700), (650, 706), (680, 670)], fill=(240, 236, 228)); d.polygon([(764, 640), (812, 700), (782, 706), (752, 670)], fill=(240, 236, 228))
    d.rounded_rectangle((120, 1070, 420, 1100), radius=10, fill=(120, 76, 56)); d.rounded_rectangle((120, 1100, 420, 1126), radius=8, fill=(150, 108, 76)); d.rectangle((150, 1126, 164, 1190), fill=(90, 66, 56)); d.rectangle((380, 1126, 394, 1190), fill=(90, 66, 56))
    for x in (860, 1010): d.rectangle((x - 5, 1040, x + 5, 1190), fill=(190, 150, 80)); d.ellipse((x - 14, 1028, x + 14, 1052), fill=(190, 150, 80))
    d.line((860, 1060, 1010, 1060), fill=(176, 50, 70), width=10)
    floor_band(d, (206, 170, 130), (184, 148, 112), edge=(150, 118, 90))
    for x in range(-100, W + 100, 150): d.line((x, HORIZON, x - 90, H), fill=(176, 140, 104), width=3)

def eiffel_view(img):
    d = ImageDraw.Draw(img); grad(d, 0, 1000, (150, 200, 244), (255, 236, 240)); clouds(d, [(220, 340, 1.3), (860, 300, 1.0), (700, 560, 0.8)])
    eiffel_tower(d, 540, 1040, 1000, (150, 160, 200), (236, 238, 248))
    d.rectangle((0, 960, W, 1050), fill=(150, 196, 150)); tree(d, 70, 1050, 130, leaf=(120, 184, 128)); tree(d, 1020, 1050, 140, leaf=(140, 196, 140))
    rng = random.Random(4)
    for _ in range(60): x, y = rng.randint(0, W), rng.randint(1010, 1040); d.ellipse((x, y, x + 36, y + 22), fill=(120, 176, 124))
    balustrade(d, 990, 1120); d.rectangle((0, 1120, W, HORIZON + 10), fill=(214, 206, 194))
    lamp(d, 430, 1180, 380)
    d.rounded_rectangle((830, 1090, 1040, 1118), radius=8, fill=(150, 108, 76)); d.rounded_rectangle((830, 1040, 1040, 1070), radius=8, fill=(176, 130, 92)); d.rectangle((850, 1118, 862, 1190), fill=(60, 66, 84)); d.rectangle((1010, 1118, 1022, 1190), fill=(60, 66, 84))
    grad(d, HORIZON + 10, H, (226, 218, 206), (206, 198, 186))
    for k in range(0, 6): d.line((0, HORIZON + 40 + k * 90, W, HORIZON + 40 + k * 90), fill=(196, 188, 176), width=2)


# ---------- batch 2 components ----------
def stall(d, cx, w, c1, c2):
    x0, x1 = cx - w // 2, cx + w // 2
    d.rectangle((x0 + 10, 600, x0 + 24, HORIZON), fill=(150, 108, 76)); d.rectangle((x1 - 24, 600, x1 - 10, HORIZON), fill=(150, 108, 76))
    awning(d, x0, x1, 500, 80, c1, c2, 6); counter(d, x0 + 6, x1 - 6, 990, (176, 130, 92), (214, 170, 128))

def flower_bucket(d, x, y, col, seed=1):
    rng = random.Random(seed)
    for k in range(4):
        fx = x + 8 + k * 11 + rng.randint(-3, 3); fy = y - 26 - rng.randint(0, 28); d.line((fx, y, fx, fy), fill=(90, 150, 90), width=3); d.ellipse((fx - 10, fy - 10, fx + 10, fy + 10), fill=lerp(col, (255, 255, 255), 0.12 * (k % 3)))
    d.rectangle((x - 4, y, x + 56, y + 50), fill=(150, 170, 190))

def suitcase(d, x0, y0, x1, y1, col):
    d.rounded_rectangle((x0, y0, x1, y1), radius=12, fill=col, outline=lerp(col, (0, 0, 0), 0.3), width=3); cx = (x0 + x1) // 2
    d.arc((cx - 16, y0 - 22, cx + 16, y0 + 8), 180, 360, fill=(70, 76, 96), width=5); d.line((x0 + 10, (y0 + y1) // 2, x1 - 10, (y0 + y1) // 2), fill=lerp(col, (0, 0, 0), 0.25), width=4)
    d.ellipse((x0 + 8, y1 - 2, x0 + 22, y1 + 8), fill=(60, 66, 84)); d.ellipse((x1 - 22, y1 - 2, x1 - 8, y1 + 8), fill=(60, 66, 84))

def sofa(d, x0, x1, ytop, col, cushion):
    d.rounded_rectangle((x0 + 20, ytop, x1 - 20, ytop + 200), radius=40, fill=col); d.rounded_rectangle((x0, ytop + 150, x1, ytop + 270), radius=30, fill=lerp(col, (0, 0, 0), 0.08))
    for ax in (x0 - 10, x1 - 50): d.rounded_rectangle((ax, ytop + 110, ax + 60, ytop + 270), radius=26, fill=lerp(col, (0, 0, 0), 0.14))
    for cx in (x0 + 90, x1 - 90): d.rounded_rectangle((cx - 40, ytop + 60, cx + 40, ytop + 160), radius=20, fill=cushion)
    d.rectangle((x0 + 20, ytop + 270, x0 + 36, ytop + 290), fill=(110, 80, 70)); d.rectangle((x1 - 36, ytop + 270, x1 - 20, ytop + 290), fill=(110, 80, 70))

def bench(d, x0, x1, ytop=1090):
    d.rounded_rectangle((x0, ytop, x1, ytop + 28), radius=8, fill=(150, 108, 76)); d.rounded_rectangle((x0, ytop - 60, x1, ytop - 28), radius=8, fill=(176, 130, 92))
    for x in (x0 + 16, x1 - 28): d.rectangle((x, ytop + 28, x + 12, ytop + 90), fill=(70, 76, 96))

# ---------- batch 2 scenes ----------
def airport(img):
    d = ImageDraw.Draw(img); grad(d, 0, HORIZON, (232, 240, 248), (244, 246, 250))
    sign(d, 540, 450, 460, 84, "AÉROPORT", (56, 96, 170), size=54)
    d.rectangle((0, 520, W, 1000), fill=(176, 214, 244)); grad(d, 520, 900, (150, 200, 244), (226, 240, 250)); d.rectangle((0, 900, W, 1000), fill=(150, 156, 170))
    for x in range(40, W, 160): d.line((x, 920, x + 90, 920), fill=(255, 255, 255), width=6)
    clouds(d, [(180, 640, 0.9), (900, 600, 0.7)])
    d.ellipse((540, 720, 980, 800), fill=(255, 255, 255), outline=(200, 206, 220), width=3); d.polygon([(600, 744), (560, 640), (626, 640), (700, 744)], fill=(255, 255, 255), outline=(200, 206, 220)); d.polygon([(600, 640), (560, 640), (572, 668), (606, 668)], fill=(210, 60, 70))
    d.polygon([(780, 780), (720, 880), (800, 880), (870, 780)], fill=(236, 240, 248), outline=(200, 206, 220)); d.rectangle((590, 764, 960, 772), fill=(56, 96, 170))
    for x in range(700, 950, 34): d.ellipse((x, 744, x + 14, 758), fill=(120, 150, 190))
    for x in range(0, W + 1, 180): d.rectangle((x, 520, x + 8, 1000), fill=(236, 240, 246))
    d.rectangle((0, 1000, W, HORIZON), fill=(226, 230, 238))
    counter(d, 30, 430, 1020, (226, 230, 240), (176, 184, 200)); d.rectangle((150, 900, 290, 990), fill=(38, 48, 74)); d.rectangle((162, 912, 278, 960), fill=(169, 208, 245)); sign(d, 230, 560, 400, 56, "ENREGISTREMENT", (56, 96, 170), size=28)
    suitcase(d, 450, 1050, 530, 1170, (210, 90, 100)); suitcase(d, 530, 1080, 590, 1175, (90, 140, 200))
    for x in (640, 740, 840): d.rounded_rectangle((x - 40, 1000, x + 40, 1090), radius=14, fill=(70, 110, 170)); d.rounded_rectangle((x - 44, 1080, x + 44, 1118), radius=12, fill=(90, 130, 190)); d.rectangle((x - 6, 1118, x + 6, 1190), fill=(60, 66, 84))
    sign(d, 940, 560, 220, 64, "PORTE 12", (210, 60, 70), size=34); counter(d, 880, W, 1030, (226, 230, 240), (176, 184, 200))
    floor_band(d, (206, 208, 222), (180, 182, 200), edge=(160, 164, 182)); checker(d, HORIZON + 14, H, (240, 242, 248), (214, 218, 232), 120)

def market(img):
    d = ImageDraw.Draw(img); grad(d, 0, HORIZON, (176, 214, 246), (255, 240, 236)); clouds(d, [(220, 300, 1.1), (900, 420, 0.8)])
    for x0, x1, col in ((0, 300, (250, 238, 214)), (300, 640, (246, 214, 206)), (640, 1080, (222, 230, 246))): d.rectangle((x0, 520, x1, HORIZON), fill=col); d.rectangle((x0, 480, x1, 530), fill=(112, 122, 152))
    sign(d, 540, 450, 360, 80, "MARCHÉ", (224, 90, 100), size=54)
    for k in range(14): x = k * 80 + 10; y = 560 + int(24 * math.sin(k / 13 * math.pi)); d.polygon([(x, y), (x + 56, y), (x + 28, y + 52)], fill=((246, 182, 205), (255, 255, 255), (169, 208, 245))[k % 3])
    stall(d, 380, 270, (230, 90, 90), (255, 255, 255)); stall(d, 660, 270, (250, 200, 80), (255, 255, 255)); stall(d, 930, 270, (110, 170, 220), (255, 255, 255))
    crate_produce(d, 262, 372, 925, (230, 70, 60), 1, 14); crate_produce(d, 388, 498, 925, (250, 160, 50), 2, 14)
    d.ellipse((560, 936, 680, 990), fill=(250, 214, 110), outline=(214, 170, 60), width=3)
    for x in (550, 700, 740): d.polygon([(x, 986), (x + 56, 986), (x + 56, 952), (x + 8, 934)], fill=(252, 226, 130), outline=(214, 170, 60))
    for i, x in enumerate(range(830, 1040, 70)): flower_bucket(d, x, 940, ((246, 150, 180), (255, 214, 120), (185, 167, 245))[i % 3], seed=i + 1)
    lamp(d, 90, 1180, 420)
    floor_band(d, (214, 208, 214), (190, 184, 196), edge=(176, 170, 184)); rng = random.Random(2)
    for _ in range(120): x, y = rng.randint(0, W), rng.randint(HORIZON + 30, 1700); d.ellipse((x, y, x + 24, y + 9), outline=(180, 174, 190))

def library(img):
    d = ImageDraw.Draw(img); grad(d, 0, HORIZON, (236, 232, 218), (224, 216, 198))
    pal = ((70, 110, 90), (150, 70, 70), (70, 90, 130), (200, 160, 80), (110, 80, 120), (236, 228, 210))
    shelf(d, 0, 520, 340, 1090, 5, pal, seed=21, frame=(120, 84, 64)); shelf(d, 740, 520, 1080, 1090, 5, pal, seed=22, frame=(120, 84, 64))
    sign(d, 540, 450, 560, 84, "BIBLIOTHÈQUE", (60, 90, 80), (255, 236, 190), size=46)
    d.rectangle((370, 560, 710, 1000), fill=(150, 108, 76)); d.rectangle((384, 574, 696, 1000), fill=(206, 230, 250)); d.pieslice((384, 530, 696, 620), 180, 360, fill=(206, 230, 250)); d.line((540, 560, 540, 1000), fill=(150, 108, 76), width=8); d.line((384, 780, 696, 780), fill=(150, 108, 76), width=8)
    d.line((690, 520, 730, 1100), fill=(176, 130, 92), width=10); d.line((660, 520, 700, 1100), fill=(176, 130, 92), width=10)
    for y in range(600, 1080, 70): d.line((668 + (y - 520) * 0.07, y, 700 + (y - 520) * 0.07 + 20, y), fill=(176, 130, 92), width=6)
    counter(d, 840, W, 1030, (120, 84, 64), (176, 130, 92)); d.rectangle((880, 940, 960, 1010), fill=(38, 48, 74)); d.rectangle((888, 948, 952, 990), fill=(169, 208, 245))
    d.rounded_rectangle((430, 1070, 780, 1100), radius=10, fill=(176, 130, 92)); d.rectangle((450, 1100, 466, 1190), fill=(120, 84, 64)); d.rectangle((744, 1100, 760, 1190), fill=(120, 84, 64))
    d.rectangle((590, 1000, 598, 1068), fill=(70, 110, 90)); d.pieslice((556, 1020, 636, 1076), 180, 360, fill=(70, 130, 100))
    for k, col in enumerate(((150, 70, 70), (70, 90, 130), (200, 160, 80))): d.rectangle((470, 1052 - k * 16, 560, 1068 - k * 16), fill=col)
    floor_band(d, (186, 150, 112), (160, 126, 94), edge=(130, 96, 72))
    for x in range(-60, W + 60, 140): d.line((x, HORIZON, x - 70, H), fill=(150, 116, 86), width=3)

def beach(img):
    d = ImageDraw.Draw(img); grad(d, 0, 880, (140, 204, 248), (236, 248, 252)); d.ellipse((800, 300, 940, 440), fill=(255, 236, 160)); clouds(d, [(220, 380, 1.2), (620, 300, 0.8)])
    grad(d, 880, 1040, (110, 196, 214), (70, 150, 190)); d.rectangle((0, 876, W, 884), fill=(236, 248, 252))
    d.polygon([(220, 790), (220, 876), (290, 876)], fill=(255, 255, 255)); d.polygon([(212, 880), (300, 880), (276, 900), (236, 900)], fill=(190, 100, 100))
    for x in range(-40, W, 120): d.arc((x, 1006, x + 120, 1050), 200, 340, fill=(255, 255, 255), width=6)
    grad(d, 1040, H, (250, 232, 196), (236, 212, 170)); d.rectangle((0, 1040, W, 1072), fill=(226, 206, 170))
    for i in range(6): d.pieslice((50, 840, 350, 1080), 180 + i * 30, 210 + i * 30, fill=(230, 80, 90) if i % 2 == 0 else (255, 255, 255))
    d.rectangle((196, 960, 204, 1180), fill=(150, 108, 76))
    d.polygon([(250, 1130), (470, 1130), (500, 1180), (220, 1180)], fill=(246, 182, 205))
    for k in range(1, 4): d.line((250 + k * 55 - k * 8, 1130, 220 + k * 70, 1180), fill=(255, 255, 255), width=8)
    d.rectangle((470, 1100, 640, 1170), fill=(226, 200, 150)); d.rectangle((470, 1060, 510, 1100), fill=(226, 200, 150)); d.rectangle((600, 1060, 640, 1100), fill=(226, 200, 150)); d.rectangle((510, 1010, 600, 1100), fill=(236, 212, 164))
    for x in (470, 600): d.polygon([(x, 1060), (x + 40, 1060), (x + 20, 1030)], fill=(210, 60, 70))
    d.line((555, 1010, 555, 970), fill=(150, 108, 76), width=4); d.polygon([(555, 970), (590, 982), (555, 994)], fill=(210, 60, 70))
    for i in range(6): d.pieslice((730, 1090, 830, 1190), i * 60, i * 60 + 60, fill=((230, 80, 90), (255, 255, 255), (80, 150, 220))[i % 3])
    for x, y in ((880, 1150), (950, 1110), (1010, 1160)): d.ellipse((x, y, x + 26, y + 18), fill=(250, 214, 220), outline=(220, 170, 180))

def courtyard(img):
    d = ImageDraw.Draw(img); grad(d, 0, 260, (190, 224, 250), (236, 246, 250)); d.rectangle((0, 260, W, HORIZON), fill=(244, 232, 208))
    for y in range(290, HORIZON, 70): d.line((0, y, W, y), fill=(232, 218, 192), width=3)
    d.rectangle((0, 200, W, 300), fill=(110, 122, 152))
    for x in (120, 860): d.rectangle((x, 140, x + 54, 210), fill=(176, 120, 104))
    for row in (390, 690):
        for x in (330, 520, 710, 900):
            d.rectangle((x - 50, row, x - 12, row + 170), fill=(120, 160, 190)); d.rectangle((x + 82, row, x + 120, row + 170), fill=(120, 160, 190)); win(d, x, row, 70, 170, frame=(120, 130, 150))
    for x in (330, 520, 710, 900):
        d.rectangle((x - 40, 870, x + 112, 884), fill=(60, 66, 84))
        for px in range(x - 36, x + 112, 22): d.line((px, 842, px, 870), fill=(60, 66, 84), width=3)
        d.rectangle((x - 40, 846, x + 112, 872), fill=(176, 100, 100))
        for px in range(x - 30, x + 110, 26): d.ellipse((px, 826, px + 22, 850), fill=((246, 150, 180), (255, 214, 120), (255, 255, 255))[(px // 26) % 3])
    d.rectangle((20, 760, 250, HORIZON), fill=(214, 200, 176)); d.rectangle((40, 800, 230, HORIZON), fill=(70, 60, 70)); d.pieslice((40, 700, 230, 900), 180, 360, fill=(70, 60, 70))
    for x in range(70, 230, 36): d.line((x, 780, x, HORIZON), fill=(90, 78, 88), width=3)
    d.ellipse((190, 960, 214, 984), fill=(255, 220, 140))
    tree(d, 440, 1150, 110, leaf=(130, 190, 130)); bench(d, 850, 1060)
    d.ellipse((600, 1118, 800, 1172), fill=(190, 198, 214), outline=(150, 158, 178), width=4); d.ellipse((620, 1126, 780, 1164), fill=(169, 208, 245)); d.rectangle((692, 1030, 708, 1146), fill=(190, 198, 214)); d.ellipse((650, 1016, 750, 1050), fill=(190, 198, 214))
    floor_band(d, (214, 208, 204), (186, 180, 178), edge=(170, 164, 164)); rng = random.Random(6)
    for _ in range(320): x, y = rng.randint(0, W), rng.randint(HORIZON + 20, 1740); d.ellipse((x, y, x + rng.randint(26, 44), y + rng.randint(10, 16)), outline=(176, 170, 170))

def apartment(img):
    d = ImageDraw.Draw(img); grad(d, 0, HORIZON, (252, 240, 228), (246, 228, 216))
    d.rectangle((0, 880, W, HORIZON), fill=(232, 204, 204)); d.rectangle((0, 872, W, 884), fill=(255, 255, 255))
    d.rectangle((24, 300, 206, HORIZON), fill=(236, 226, 214)); d.rectangle((40, 316, 190, HORIZON), fill=(150, 108, 76))
    for y0, y1 in ((340, 660), (700, 1060)): d.rounded_rectangle((60, y0, 170, y1), radius=10, outline=(120, 84, 64), width=5)
    d.ellipse((150, 850, 176, 876), fill=(255, 220, 140))
    d.rectangle((530, 340, 830, 1040), fill=(255, 255, 255)); d.rectangle((548, 358, 812, 1022), fill=(190, 224, 250)); clouds(d, [(640, 460, 0.45)])
    eiffel_tower(d, 680, 1022, 520, (170, 180, 214), (190, 224, 250)); d.line((680, 358, 680, 1022), fill=(255, 255, 255), width=8); d.line((548, 690, 812, 690), fill=(255, 255, 255), width=8)
    d.line((480, 330, 880, 330), fill=(150, 108, 76), width=8)
    d.polygon([(500, 330), (580, 330), (560, 1040), (490, 1040)], fill=(246, 182, 205)); d.polygon([(860, 330), (780, 330), (800, 1040), (870, 1040)], fill=(246, 182, 205))
    frame_art(d, 250, 540, 120, 160, 31); frame_art(d, 410, 560, 100, 130, 32)
    shelf(d, 880, 420, 1070, 1120, 5, ((176, 70, 80), (70, 110, 150), (90, 140, 110), (220, 170, 80), (236, 230, 214)), seed=23)
    floor_band(d, (206, 160, 118), (180, 134, 98), edge=(150, 108, 76))
    for x in range(-60, W + 60, 140): d.line((x, HORIZON, x - 70, H), fill=(170, 124, 90), width=3)
    d.ellipse((150, 1140, 720, 1270), fill=(236, 196, 200)); d.ellipse((190, 1156, 680, 1254), fill=(246, 214, 216))
    sofa(d, 230, 590, 880, (150, 190, 220), (246, 182, 205)); round_table(d, 400, 1100, 200, (246, 214, 170))
    for cx in (350, 450): d.ellipse((cx - 18, 1096, cx + 18, 1112), fill=(255, 255, 255), outline=(200, 204, 214))
    lamp(d, 840, 1180, 520)

EXTRA = {
    "supermarket": _make("supermarket", supermarket, {"entrance": 110, "fruit stand": 400, "shelves": 660, "checkout": 920}, ["supermarché", "grocery", "grocery store", "store"]),
    "bookstore": _make("bookstore", bookstore, {"entrance": 110, "shelves": 400, "reading corner": 720, "counter": 960}, ["librairie", "book store", "bookshop"]),
    "restaurant": _make("restaurant", restaurant, {"entrance": 110, "table": 330, "window table": 640, "counter": 930}, ["resto", "dining room"]),
    "train station": _make("train station", train_station, {"entrance": 110, "ticket window": 340, "departures board": 560, "platform": 900}, ["gare", "station", "railway station", "train"]),
    "museum": _make("museum", museum, {"entrance": 110, "painting": 380, "statue": 690, "bench": 960}, ["musée", "gallery", "art museum"]),
    "eiffel": _make("eiffel", eiffel_view, {"steps": 130, "viewpoint": 360, "bench": 930}, ["eiffel tower", "tour eiffel", "trocadéro", "viewpoint", "eiffel viewpoint"]),
    "airport": _make("airport", airport, {"entrance": 110, "check-in": 330, "seats": 740, "gate": 940}, ["aéroport", "aeroport", "terminal"]),
    "market": _make("market", market, {"entrance": 110, "fruit stall": 380, "cheese stall": 660, "flower stall": 930}, ["marché", "farmers market", "street market"]),
    "library": _make("library", library, {"entrance": 110, "shelves": 320, "reading table": 600, "desk": 940}, ["bibliothèque", "bibliotheque"]),
    "beach": _make("beach", beach, {"umbrella": 200, "sandcastle": 540, "shore": 900}, ["plage", "seaside"]),
    "courtyard": _make("courtyard", courtyard, {"archway": 130, "tree": 440, "fountain": 700, "bench": 960}, ["cour", "patio", "yard"]),
    "apartment": _make("apartment", apartment, {"door": 120, "sofa": 400, "window": 680, "bookshelf": 960}, ["appartement", "flat", "living room"]),
}
