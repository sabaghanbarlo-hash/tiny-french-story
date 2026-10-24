"""Characters cut out of the reference picture (assets/reference/characters.png).

extract(reference_png, out_dir)  -> writes adrien.png / marinette.png (+ *_blank.png without eyes and mouth) and meta.json
ref_sprite(name, mouth, blink)   -> animated RGBA sprite built from those cutouts (None if the assets are not there)
Needs opencv-python-headless only for extract(); rendering only needs Pillow.
"""
import functools, json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sprites")
# Locations measured on the 1086x1448 reference picture (x0, y0, x1, y1)
CUT = {
    "Adrien": dict(rect=(60, 255, 500, 800), bottom=792, forbid=[(170, 246, 352, 316)],
                   eyes=[(256, 551, 40, 46), (371, 540, 36, 46)], mouth=(316, 609, 28, 14)),
    "Marinette": dict(rect=(625, 350, 1010, 805), bottom=796, forbid=[],
                      eyes=[(742, 578, 44, 46), (858, 588, 48, 46)], mouth=(796, 644, 30, 14)),
}


def _blank_face(img, rgb, c):
    import cv2
    H, W = rgb.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.int16)
    r = rgb.astype(np.int16); tot = r.sum(2)
    hair = (r[:, :, 2] > r[:, :, 1] + 18) & (tot < 420)
    skin_like = (r[:, :, 0] > 225) & (r[:, :, 1] > 190) & (r[:, :, 2] > 160) & ((r[:, :, 0] - r[:, :, 2]) > 25) & ((r[:, :, 0] - r[:, :, 2]) < 80)
    out = img.copy().astype(np.float32)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    parts = [(ex, ey, rx, ry) for ex, ey, rx, ry in c["eyes"]] + [(c["mouth"][0], c["mouth"][1], c["mouth"][2] + 4, c["mouth"][3] + 4)]
    for ex, ey, rx, ry in parts:
        ell = (((xx - ex) / (rx + 14)) ** 2 + ((yy - ey) / (ry + 12)) ** 2) <= 1
        tight = (((xx - ex) / (rx + 6)) ** 2 + ((yy - ey) / (ry + 4)) ** 2) <= 1
        golden = (r[:, :, 0] > 150) & ((r[:, :, 0] - r[:, :, 1]) > 25) & ((r[:, :, 1] - r[:, :, 2]) > 30)   # brows / blond hair
        limit = 500 if (ex, ey, rx, ry) == (c["mouth"][0], c["mouth"][1], c["mouth"][2] + 4, c["mouth"][3] + 4) else 470
        hole = ell & ((tot < limit) | ((r.min(2) > 222) & tight)) & ~hair & ~golden
        hole = cv2.dilate(hole.astype(np.uint8), k) > 0
        ring = (((xx - ex) / (rx + 34)) ** 2 + ((yy - ey) / (ry + 30)) ** 2) <= 1
        px = rgb[ring & ~hole & skin_like]
        fill = np.median(px, axis=0) if len(px) else np.array([252, 228, 205])
        alpha = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), 2.0)[:, :, None]
        out = out * (1 - alpha) + fill[::-1].astype(np.float32) * alpha
    return out.astype(np.uint8)


def extract(ref_path, out_dir):
    import cv2
    img = cv2.imread(ref_path)
    if img is None:
        raise FileNotFoundError(f"Cannot read the reference picture: {ref_path}")
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    os.makedirs(out_dir, exist_ok=True)
    meta = {}
    for name, c in CUT.items():
        x0, y0, x1, y1 = c["rect"]; w, h = x1 - x0, y1 - y0
        mask = np.full(img.shape[:2], cv2.GC_BGD, np.uint8)
        mask[y0:y1, x0:x1] = cv2.GC_PR_BGD
        mask[y0 + int(h * 0.08):y1, x0 + int(w * 0.12):x1 - int(w * 0.12)] = cv2.GC_PR_FGD
        mask[y0 + int(h * 0.35):y1 - 10, x0 + int(w * 0.3):x1 - int(w * 0.3)] = cv2.GC_FGD
        for fx0, fy0, fx1, fy1 in c["forbid"]:
            mask[fy0:fy1, fx0:fx1] = cv2.GC_BGD
        gx0, gy0, gx1, gy1 = max(0, x0 - 20), max(0, y0 - 20), min(img.shape[1], x1 + 20), min(img.shape[0], y1 + 20)   # work on a crop: far less memory
        sub = mask[gy0:gy1, gx0:gx1].copy()
        cv2.grabCut(np.ascontiguousarray(img[gy0:gy1, gx0:gx1]), sub, None, np.zeros((1, 65)), np.zeros((1, 65)), 8, cv2.GC_INIT_WITH_MASK)
        mask[gy0:gy1, gx0:gx1] = sub
        m = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
        m[c["bottom"]:, :] = 0
        r, g, b = rgb[:, :, 0].astype(np.int16), rgb[:, :, 1].astype(np.int16), rgb[:, :, 2].astype(np.int16)
        m[((b - r) > 8) & ((r + g + b) > 540)] = 0                       # pale-blue window showing through gaps
        n, lab, st, _ = cv2.connectedComponentsWithStats(m)
        if n > 1:
            m = np.where(lab == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])), 255, 0).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        k9 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k9, iterations=2)       # close the little holes GrabCut leaves in dark eyes
        ff = m.copy(); fm = np.zeros((m.shape[0] + 2, m.shape[1] + 2), np.uint8)
        cv2.floodFill(ff, fm, (0, 0), 255); m = m | cv2.bitwise_not(ff)    # fill any remaining enclosed holes
        m[((b - r) > 8) & ((r + g + b) > 540)] = 0                       # window colours again, after the hole-closing
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(m)
        if n > 1:
            m = np.where(lab == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])), 255, 0).astype(np.uint8)
        m = cv2.erode(m, np.ones((3, 3), np.uint8))
        m = cv2.GaussianBlur(m, (0, 0), 1.0)
        # blank face: eyes and mouth painted over with the surrounding skin colour
        blank = _blank_face(img, rgb, c)
        ys, xs = np.where(m > 8); bx0, by0, bx1, by1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
        for suffix, src in (("", img), ("_blank", blank)):
            rgba = np.dstack([cv2.cvtColor(src, cv2.COLOR_BGR2RGB), m])[by0:by1, bx0:bx1]
            Image.fromarray(rgba, "RGBA").save(os.path.join(out_dir, name.lower() + suffix + ".png"), optimize=True)
        mx, my = c["mouth"][:2]
        skin = np.median(rgb[my - 40:my - 20, mx - 15:mx + 15].reshape(-1, 3), axis=0).astype(int).tolist()
        meta[name] = dict(offset=[int(bx0), int(by0)], eyes=c["eyes"], mouth=c["mouth"], skin=skin)
    json.dump(meta, open(os.path.join(out_dir, "meta.json"), "w"))
    return meta


@functools.lru_cache(None)
def _load(name):
    p = os.path.join(ASSET_DIR, name.lower() + ".png")
    if not (os.path.exists(p) and os.path.exists(os.path.join(ASSET_DIR, "meta.json"))):
        return None
    meta = json.load(open(os.path.join(ASSET_DIR, "meta.json")))[name]
    return Image.open(p).convert("RGBA"), Image.open(os.path.join(ASSET_DIR, name.lower() + "_blank.png")).convert("RGBA"), meta


@functools.lru_cache(None)
def ref_sprite(name, mouth, blink, scale=1.0):
    got = _load(name)
    if got is None:
        return None
    base, blank, meta = got
    ox, oy = meta["offset"]
    im = base.copy(); d = ImageDraw.Draw(im)
    ink = (62, 34, 46, 255)
    if blink:
        for ex, ey, rx, ry in meta["eyes"]:
            box = (ex - rx - 22 - ox, ey - ry - 18 - oy, ex + rx + 22 - ox, ey + ry + 18 - oy)
            im.paste(blank.crop(box), box[:2])
        d = ImageDraw.Draw(im)
        for ex, ey, rx, ry in meta["eyes"]:
            cx, cy = ex - ox, ey - oy + 6
            d.arc((cx - rx, cy - 16, cx + rx, cy + 22), 20, 160, fill=ink, width=7)
            d.ellipse((cx - rx - 2, cy + 2, cx - rx + 8, cy + 12), fill=ink)
    if mouth:
        mx, my, rx, ry = meta["mouth"]
        box = (mx - rx - 14 - ox, my - ry - 14 - oy, mx + rx + 14 - ox, my + ry + 14 - oy)
        im.paste(blank.crop(box), box[:2]); d = ImageDraw.Draw(im)
        cx, cy = mx - ox, my - oy + 4
        a, b = (11, 9) if mouth == 1 else (15, 15)
        d.ellipse((cx - a, cy - b + 3, cx + a, cy + b + 3), fill=(112, 44, 60, 255))
        if mouth == 2:
            d.ellipse((cx - 9, cy + 6, cx + 9, cy + 17), fill=(232, 120, 134, 255))
    return im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
