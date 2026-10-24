#!/usr/bin/env python3
"""Tiny French "Small" videos: two friends (Adrien and Marinette) sit in a place and chat.

Script (.txt) -> 1080x1920 MP4 + .srt + .caption.txt + .cover.png + .json.
Free stack: edge-tts French voices, Pillow drawing, FFmpeg.

Script format:
    title: Meeting for the First Time
    episode: 1
    scene: cafe            (cafe, bakery, park, classroom, station, store - or leave out for auto)
    Adrien: Bonjour ! | Hello!
    Marinette: Salut ! | Hi! | sa-LU          <- optional 3rd part: pronunciation hint
    vocab: bonjour | hello
"""
import argparse, asyncio, functools, glob, json, math, os, random, re, subprocess, sys, tempfile, time, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sprites import sprite, CHARS  # noqa: E402

W, H, FPS, SR = 1080, 1920, 30, 24000
CHAR_Y, TABLE_TOP, CARD_Y = 300, 885, 1040
BRAND = (122, 150, 204)
MAX_CHARS = 8000
SCENES = {
    "cafe": dict(top=(255, 244, 230), bot=(248, 228, 208), floor=(214, 170, 122), table=(224, 176, 126), edge=(190, 142, 98)),
    "bakery": dict(top=(255, 240, 226), bot=(250, 222, 200), floor=(206, 160, 116), table=(236, 196, 150), edge=(196, 150, 108)),
    "park": dict(top=(190, 226, 250), bot=(236, 248, 238), floor=(150, 204, 126), table=(196, 158, 114), edge=(150, 116, 82)),
    "classroom": dict(top=(240, 247, 236), bot=(250, 252, 244), floor=(206, 176, 136), table=(226, 196, 150), edge=(176, 142, 102)),
    "station": dict(top=(196, 224, 246), bot=(236, 246, 252), floor=(156, 156, 170), table=(238, 204, 100), edge=(126, 126, 140)),
    "store": dict(top=(232, 246, 255), bot=(246, 252, 255), floor=(214, 218, 226), table=(124, 198, 172), edge=(86, 152, 130)),
}
SCENE_KEYWORDS = {
    "bakery": ["boulangerie", "croissant", "baguette", "pain", "bakery", "bread", "pastry"],
    "park": ["parc", "jardin", "banc", "park", "garden", "bench", "picnic"],
    "classroom": ["classe", "école", "ecole", "cours", "professeur", "classroom", "school", "teacher", "lesson"],
    "station": ["gare", "train", "métro", "metro", "billet", "station", "ticket", "platform"],
    "store": ["supermarché", "supermarche", "magasin", "marché", "marche", "courses", "store", "market", "shop"],
    "cafe": ["café", "cafe", "thé", "coffee", "tea", "chocolat"],
}
ALIASES = {"supermarket": "store", "market": "store", "shop": "store", "metro": "station", "school": "classroom", "garden": "park"}


class ScriptProblem(Exception):
    pass


# ---------- text helpers ----------
@functools.lru_cache(None)
def font(size, bold=True):
    names = ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"] if bold else ["DejaVuSans.ttf", "LiberationSans-Regular.ttf"]
    for n in names:
        g = sorted(glob.glob(f"/usr/share/fonts/**/{n}", recursive=True))
        if g:
            return ImageFont.truetype(g[0], size)
    return ImageFont.load_default()


def wrap(text, f, maxw):
    out, cur = [], ""
    for t in text.split():
        trial = (cur + " " + t) if cur else t
        if f.getlength(trial) > maxw and cur:
            out.append(cur); cur = t
        else:
            cur = trial
    return out + [cur] if cur else out


# ---------- script ----------
def parse_story(text):
    if len(text) > MAX_CHARS:
        raise ScriptProblem(f"The script is too long ({len(text)} characters; limit {MAX_CHARS}).")
    meta, lines, vocab = {"title": "", "scene": "auto", "episode": ""}, [], []
    for n, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r"^(title|scene|episode)\s*:\s*(.+)$", s, re.I)
        if m:
            meta[m[1].lower()] = m[2].strip(); continue
        m = re.match(r"^vocab\s*:\s*(.+)$", s, re.I)
        if m:
            p = [x.strip() for x in m[1].split("|")]
            if len(p) not in (2, 3) or not all(p):
                raise ScriptProblem(f"line {n}: vocab needs 'French | English' (or 'French | pronunciation | English').")
            vocab.append(dict(fr=p[0], pron=p[1] if len(p) == 3 else "", en=p[-1])); continue
        m = re.match(r"^([A-Za-zÀ-ÿ]+)\s*[:：]\s*(.+)$", s)
        if m and m[1].capitalize() in CHARS:
            p = [x.strip() for x in m[2].split("|")]
            if len(p) < 2 or not p[0] or not p[1]:
                raise ScriptProblem(f"line {n}: add the English after a | sign, like 'Adrien: Bonjour ! | Hello!'.")
            lines.append(dict(speaker=m[1].capitalize(), fr=p[0], en=p[1], pron=p[2] if len(p) > 2 else "")); continue
        raise ScriptProblem(f"line {n}: can't read this line (speakers are {' and '.join(CHARS)}): {s[:60]}")
    if not meta["title"]:
        raise ScriptProblem("Add a 'title:' line at the top.")
    if not lines:
        raise ScriptProblem("No dialogue lines found. Use lines like 'Adrien: Bonjour ! | Hello!'.")
    return meta, lines, vocab[:5]


def pick_scene(meta, lines):
    sc = ALIASES.get(meta["scene"].lower(), meta["scene"].lower())
    if sc in SCENES:
        return sc
    if sc != "auto":
        raise ScriptProblem(f"unknown scene '{meta['scene']}'. Scenes: {', '.join(SCENES)} (or auto).")
    text = (meta["title"] + " " + " ".join(l["fr"] + " " + l["en"] for l in lines)).lower()
    best, score = "cafe", 0
    for name, kws in SCENE_KEYWORDS.items():
        n = sum(text.count(k) for k in kws)
        if n > score:
            best, score = name, n
    return best


# ---------- audio ----------
def write_wav(path, x):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def read_wav(path):
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def synth(text, voice, out_wav, rate, dummy=False, lang="fr"):
    if dummy:
        n = int(max(1.0, len(text) * 0.08) * SR); t = np.arange(n) / SR
        write_wav(out_wav, 0.4 * np.sin(2 * np.pi * 220 * t) * np.abs(np.sin(2 * np.pi * 3.5 * t)) ** 0.7); return
    mp3, ok, last = out_wav + ".mp3", False, None
    for attempt in range(1, 6):
        try:
            import edge_tts
            asyncio.run(edge_tts.Communicate(text, voice, rate=rate).save(mp3)); ok = True; break
        except Exception as e:
            last = e; print(f"edge-tts attempt {attempt}/5 failed ({e})", file=sys.stderr)
            if attempt < 5:
                time.sleep(4 * attempt)
    if not ok:
        if os.environ.get("STRICT_VOICE") == "1":
            sys.exit("::error::The natural voice service is unavailable right now. Re-run in a little while.")
        print(f"::warning::edge-tts unavailable ({last}); using the lower-quality gTTS voice", file=sys.stderr)
        from gtts import gTTS
        gTTS(text, lang=lang).save(mp3)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-ar", str(SR), "-ac", "1", out_wav], check=True)


def mouth_levels(audio, n):
    spf = SR / FPS
    rms = np.array([np.sqrt(np.mean(audio[int(i * spf):int((i + 1) * spf)] ** 2) + 1e-12) if int(i * spf) < len(audio) else 0 for i in range(n)])
    ref = np.percentile(rms[rms > 1e-3], 90) if (rms > 1e-3).any() else 1
    lv = np.clip(rms / ref, 0, 1.2); sm = lv.copy(); sm[1:-1] = 0.5 * lv[1:-1] + 0.25 * (lv[:-2] + lv[2:])
    return np.where(sm < 0.15, 0, np.where(sm < 0.55, 1, 2))


# ---------- drawing ----------
def vgrad(w, h, a, b):
    arr = np.zeros((h, w, 3), np.uint8)
    for i in range(3):
        arr[:, :, i] = np.linspace(a[i], b[i], h)[:, None]
    return Image.fromarray(arr).convert("RGBA")


def pill(text, fill, fg=(255, 255, 255), size=32):
    f = font(size); tw = int(f.getlength(text)) + 56; hh = int(size * 1.8)
    im = Image.new("RGBA", (tw, hh), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, tw - 1, hh - 1), radius=hh // 2, fill=fill)
    d.text((tw / 2, hh / 2), text, font=f, fill=fg, anchor="mm"); return im


def eiffel(d, cx, base, h, col):
    w = h * 0.34
    d.polygon([(cx - w / 2, base), (cx - w * 0.06, base - h), (cx + w * 0.06, base - h), (cx + w / 2, base)], fill=col)
    d.rectangle((cx - w * 0.3, base - h * 0.36, cx + w * 0.3, base - h * 0.325), fill=col)
    d.rectangle((cx - w * 0.17, base - h * 0.64, cx + w * 0.17, base - h * 0.61), fill=col)
    d.polygon([(cx - w * 0.22, base), (cx + w * 0.22, base), (cx, base - h * 0.22)], fill=tuple(min(255, c + 30) for c in col))


def make_scene(scene, meta):
    sc = SCENES[scene]
    bg = vgrad(W, H, sc["top"], sc["bot"]); d = ImageDraw.Draw(bg)
    if scene in ("cafe", "bakery", "classroom", "station", "store"):
        d.rounded_rectangle((220, 250, 880, 800), radius=30, fill=(190, 198, 232))
        d.rounded_rectangle((240, 270, 860, 780), radius=18, fill=(196, 230, 250))
        d.rounded_rectangle((240, 530, 860, 780), radius=0, fill=(176, 214, 176))
        for x, y, r in ((300, 600, 60), (400, 640, 70), (700, 610, 64), (800, 650, 74)):
            d.ellipse((x - r, y - r * 0.8, x + r, y + r * 0.8), fill=(150, 200, 152))
        for cx, cy in ((330, 360), (700, 340)):
            d.ellipse((cx - 60, cy - 20, cx + 60, cy + 20), fill=(236, 246, 254))
        eiffel(d, 540, 700, 430, (140, 176, 222))
        d.rectangle((534, 270, 546, 780), fill=(190, 198, 232)); d.rectangle((240, 520, 860, 532), fill=(190, 198, 232))
    if scene in ("cafe", "bakery"):
        d.rectangle((0, 560, 90, 640), fill=(196, 140, 96)); d.rectangle((0, 640, 120, 660), fill=(196, 140, 96))
        for cx, cy, r in ((40, 470, 70), (90, 420, 56), (20, 380, 50)):
            d.ellipse((cx - r * 0.5, cy - r, cx + r * 0.5, cy + r * 0.6), fill=(116, 160, 120))
        d.rounded_rectangle((990, 180, 1080, 760), radius=8, fill=(118, 92, 72)); d.rectangle((1000, 192, 1080, 748), fill=(58, 62, 66))
        eiffel(d, 1050, 400, 150, (220, 220, 224))
    if scene == "bakery":
        d.polygon([(220, 190), (880, 190), (920, 260), (180, 260)], fill=(236, 120, 130))
        for x in range(180, 920, 80):
            d.polygon([(x, 190), (x + 40, 190), (x + 40, 260), (x, 260)], fill=(255, 250, 246))
    elif scene == "park":
        d.ellipse((140, 280, 320, 460), fill=(252, 234, 150))
        for x in (760, 960):
            d.rectangle((x - 18, 520, x + 18, 820), fill=(122, 88, 66)); d.ellipse((x - 150, 300, x + 150, 600), fill=(96, 176, 108))
        for cx, cy in ((420, 360), (580, 300)):
            d.ellipse((cx - 80, cy - 30, cx + 80, cy + 30), fill=(255, 255, 255)); d.ellipse((cx - 30, cy - 55, cx + 50, cy + 10), fill=(255, 255, 255))
        eiffel(d, 540, 700, 330, (150, 184, 220))
    elif scene == "classroom":
        d.rounded_rectangle((100, 240, 980, 640), radius=18, fill=(150, 112, 78)); d.rounded_rectangle((120, 260, 960, 620), radius=10, fill=(52, 98, 80))
        d.text((540, 380), "Bonjour !", font=font(110), fill=(244, 244, 236), anchor="mm"); d.text((540, 520), "a  b  c  d  é", font=font(70), fill=(244, 230, 140), anchor="mm")
    elif scene == "station":
        d.rounded_rectangle((300, 150, 780, 240), radius=24, fill=(60, 80, 120)); d.text((540, 195), "GARE", font=font(54), fill="white", anchor="mm")
    elif scene == "store":
        d.rectangle((0, 140, W, 230), fill=(52, 160, 120)); d.text((540, 185), "SUPERMARCHÉ  ·  OUVERT", font=font(48), fill="white", anchor="mm")
    d.rectangle((0, TABLE_TOP, W, H), fill=sc["floor"])
    for y in range(TABLE_TOP + 150, H, 100):
        d.line([(0, y), (W, y)], fill=tuple(int(v * 0.93) for v in sc["floor"]), width=3)
    ep = f"Ep.{meta['episode']}  ·  " if meta.get("episode") else ""
    d.rounded_rectangle((60, 78, 1020, 232), radius=62, fill=(250, 247, 242, 245))
    d.text((112, 106), "TINY FRENCH", font=font(30), fill=BRAND)
    size = 54
    while size > 28 and font(size).getlength(ep + meta["title"]) > 860:
        size -= 2
    d.text((112, 152), ep + meta["title"], font=font(size), fill=(52, 54, 66))
    fg = Image.new("RGBA", (W, 175), (0, 0, 0, 0)); g = ImageDraw.Draw(fg)
    g.rectangle((0, 55, W, 125), fill=sc["table"]); g.rectangle((0, 125, W, 175), fill=sc["edge"])
    for x in (170, 830):
        if scene in ("cafe", "bakery"):
            g.rounded_rectangle((x, 6, x + 96, 66), radius=20, fill=(255, 252, 248)); g.ellipse((x + 78, 20, x + 122, 52), outline=(255, 252, 248), width=9)
            g.ellipse((x + 12, 10, x + 84, 24), fill=(226, 210, 196))
    return bg, fg


def card_image(tag, tag_color, parts, min_h=380):
    body = sum(p[3] for p in parts); h = max(min_h, body + 150); cw = 960
    size = (cw + 80, h + 80)
    m = Image.new("L", size, 0); ImageDraw.Draw(m).rounded_rectangle((40, 52, 40 + cw, 52 + h), radius=56, fill=90)
    sh_ = Image.new("RGBA", size, (120, 90, 70, 0)); sh_.putalpha(m.filter(ImageFilter.GaussianBlur(16)))
    img = Image.alpha_composite(Image.new("RGBA", size, (0, 0, 0, 0)), sh_); d = ImageDraw.Draw(img)
    d.rounded_rectangle((40, 40, 40 + cw, 40 + h), radius=56, fill=(250, 248, 243, 247))
    y = 40 + 56 + (h - 56 - 36 - body) / 2
    for text, f, color, adv in parts:
        if f:
            d.text((40 + cw / 2, y), text, font=f, fill=color, anchor="ma")
        y += adv
    p = pill(tag, tag_color); img.paste(p, (84, 14), p); return img


def line_card(ln):
    maxw = 840
    big = next((font(s) for s in (64, 58, 52, 46) if len(wrap(ln["fr"], font(s), maxw)) <= 2), font(46))
    pr, en = font(36, False), font(40, False)
    parts = [(t, big, (46, 48, 60), 80) for t in wrap(ln["fr"], big, maxw)]
    if ln["pron"]:
        parts += [("", None, None, 10)] + [(t, pr, (128, 152, 204), 48) for t in wrap(ln["pron"], pr, maxw)]
    parts += [("", None, None, 16)] + [(t, en, (84, 86, 96), 54) for t in wrap(ln["en"], en, maxw)]
    return card_image(ln["speaker"], CHARS[ln["speaker"]]["accent"], parts)


def vocab_card(vocab, active):
    parts = []
    for i, v in enumerate(vocab):
        fc, sc = ((46, 48, 60), (116, 120, 134)) if i == active else ((150, 152, 164), (176, 178, 188))
        parts.append((v["fr"], font(50), fc, 64)); parts.append((v["en"] + (f'   ({v["pron"]})' if v["pron"] else ""), font(31, False), sc, 58))
    return card_image("Today's tiny words", BRAND, parts, min_h=420)


# ---------- build ----------
def build(text, rate, dummy, tmp):
    meta, lines, vocab = parse_story(text)
    meta["scene"] = pick_scene(meta, lines)
    chunks, t = [np.zeros(int(0.6 * SR), np.float32)], 0.6
    for i, ln in enumerate(lines):
        wav = os.path.join(tmp, f"l{i}.wav"); synth(ln["fr"], CHARS[ln["speaker"]]["voice"], wav, rate, dummy)
        x = read_wav(wav); ln["start"], ln["end"] = t, t + len(x) / SR
        chunks += [x, np.zeros(int(0.5 * SR), np.float32)]; t = ln["end"] + 0.5
    vstart, talk = t, list(lines)
    for j, v in enumerate(vocab):
        v["start"] = t
        for k, (txt, kind) in enumerate(((v["fr"], "fr"), ("means " + v["en"], "en"), (v["fr"], "fr"))):
            wav = os.path.join(tmp, f"v{j}_{k}.wav")
            if kind == "fr":
                synth(txt, CHARS["Marinette"]["voice"], wav, "-25%", dummy)
            else:
                synth(txt, "en-US-AriaNeural", wav, "+0%", dummy, lang="en")
            x = read_wav(wav)
            if kind == "fr":
                talk.append(dict(speaker="Marinette", start=t, end=t + len(x) / SR))
            gap = 0.45 if k < 2 else 0.9
            chunks += [x, np.zeros(int(gap * SR), np.float32)]; t += len(x) / SR + gap
        v["end"] = t
    total = t + (0.6 if vocab else 1.2)
    chunks.append(np.zeros(int((total - t) * SR) + SR, np.float32))
    audio = np.concatenate(chunks); audio = audio / max(0.01, np.abs(audio).max()) * 0.9
    n = int(total * FPS); mouth = mouth_levels(audio, n)
    bg, fg = make_scene(meta["scene"], meta)
    cards = [line_card(l) for l in lines]; vcards = [vocab_card(vocab, j) for j in range(len(vocab))]
    pills = {(nm, a): pill(nm, CHARS[nm]["accent"] if a else (226, 214, 206), (255, 255, 255) if a else (130, 112, 108)) for nm in CHARS for a in (0, 1)}

    def frame(i):
        tt = i / FPS; fr = bg.copy()
        cur = next((k for k, l in enumerate(talk) if l["start"] - 0.02 <= tt <= l["end"] + 0.1), None)
        for nm, c in CHARS.items():
            sp = cur is not None and talk[cur]["speaker"] == nm
            bob = 5 * abs(math.sin(tt * 7)) if sp and mouth[i] else 2 * math.sin(tt * 2 + (0 if nm == "Adrien" else 1.7))
            blink = ((i + (0 if nm == "Adrien" else 41)) % 97) < 4
            s = sprite(nm, int(mouth[i]) if sp else 0, blink)
            fr.paste(s, (c["x"], int(CHAR_Y - bob)), s)
            p = pills[(nm, int(sp))]; fr.paste(p, (c["x"] + s.width // 2 - p.width // 2, 322), p)
        fr.paste(fg, (0, TABLE_TOP - 55), fg)
        card, t0 = None, 0
        if tt >= vstart and vcards:
            j = max((j for j, v in enumerate(vocab) if tt >= v["start"]), default=0); card, t0 = vcards[j], vstart
        else:
            k = max((k for k, l in enumerate(lines) if tt >= l["start"] - 0.02), default=None)
            if k is not None:
                card, t0 = cards[k], lines[k]["start"]
        if card:
            f = min(1, (tt - t0) / 0.2); dy = int(24 * (1 - f))
            if f < 1:
                card = card.copy(); card.putalpha(card.getchannel("A").point(lambda v: int(v * f)))
            fr.paste(card, (20, CARD_Y - 40 + dy), card)
        return fr.convert("RGB")

    return meta, lines, vocab, audio, n, frame


def srt_time(t):
    ms = int(round(t * 1000)); return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def caption(meta, vocab):
    out = f"Learn French with Adrien & Marinette 🇫🇷 — {meta['title']}\n\n"
    if vocab:
        out += "Today's tiny French:\n" + "\n".join(f"• {v['fr']} — {v['en']}" for v in vocab) + "\n"
    return out + "\nSave this to practice later! 💌\nSmall steps. Big dreams.\n\n#learnfrench #frenchforbeginners #french #frenchlanguage #frenchlesson #languagelearning #tinyfrench"


def main():
    ap = argparse.ArgumentParser(description="Tiny French 'Small' video")
    ap.add_argument("script"); ap.add_argument("-o", "--out", default="output")
    ap.add_argument("--rate", default="-10%"); ap.add_argument("--dummy-audio", action="store_true", help="TEST ONLY: tones instead of voices")
    ap.add_argument("--check", action="store_true", help="only check the script")
    ap.add_argument("--preview", help="save one PNG frame and exit"); ap.add_argument("--progress-file")
    a = ap.parse_args()
    text = open(a.script, encoding="utf-8").read()
    try:
        meta, lines, vocab = parse_story(text); pick_scene(meta, lines)
    except ScriptProblem as e:
        print("::error title=Script problem::" + str(e).replace("\n", "%0A")); sys.exit(1)
    if a.check:
        print(f"Script OK: {meta['title']} ({len(lines)} lines, scene {pick_scene(meta, lines)})"); return
    stem = os.path.splitext(os.path.basename(a.script))[0]; os.makedirs(a.out, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        meta, lines, vocab, audio, n, frame = build(text, a.rate, a.dummy_audio, tmp)
        if a.preview:
            l = lines[min(1, len(lines) - 1)]; frame(int((l["start"] + 0.5) * FPS)).save(a.preview); return
        wav = os.path.join(tmp, "final.wav"); write_wav(wav, audio)
        mp4 = os.path.join(a.out, stem + ".mp4")
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", mp4], stdin=subprocess.PIPE)
        for i in range(n):
            p.stdin.write(frame(i).tobytes())
            if a.progress_file and i % 30 == 0:
                open(a.progress_file, "w").write(json.dumps({"done": i, "total": n}))
        p.stdin.close()
        if p.wait() != 0:
            sys.exit("::error::FFmpeg failed while encoding the video.")
        l = lines[min(1, len(lines) - 1)]; frame(int((l["start"] + 0.6) * FPS)).save(os.path.join(a.out, stem + ".cover.png"))
    with open(os.path.join(a.out, stem + ".srt"), "w", encoding="utf-8") as f:
        for i, l in enumerate(lines, 1):
            f.write(f"{i}\n{srt_time(l['start'])} --> {srt_time(l['end'])}\n{l['fr']}\n{l['en']}\n\n")
    open(os.path.join(a.out, stem + ".caption.txt"), "w", encoding="utf-8").write(caption(meta, vocab))
    json.dump(dict(title=meta["title"], episode=meta["episode"], scene=meta["scene"], seconds=round(n / FPS, 1), width=W, height=H, fps=FPS, lines=len(lines), vocab=len(vocab)),
              open(os.path.join(a.out, stem + ".json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(f"Wrote {mp4} ({n / FPS:.1f}s)")


if __name__ == "__main__":
    main()
