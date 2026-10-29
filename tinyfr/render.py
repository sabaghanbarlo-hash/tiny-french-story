"""Tiny French - vertical (1080x1920) Reel renderer. Stage 2: parser, French voices, SRT, cards, placeholder figures."""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .config import *
from .parser import Say, Direction, SceneChange
from .voice import synth, read_wav, write_wav
from .srt import write_srt

from .fonts import font
from . import acting, scenes as SC, rig

NB = "\u00a0"
def frtypo(s):
    """French spacing: keep ! ? : ; and guillemets attached to their word."""
    for p in "!?:;":
        s = s.replace(" " + p, NB + p)
    return s.replace("\u00ab ", "\u00ab" + NB).replace(" \u00bb", NB + "\u00bb")

def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for w in frtypo(text).split(" "):
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def block(d, cx, y, text, size, fill, maxw, bold=True, gap=1.18, maxlines=None):
    """Centered wrapped text; shrinks the font to fit maxlines. Returns bottom y."""
    s = size
    while True:
        f = font(s, bold); lines = wrap(d, text, f, maxw)
        if maxlines is None or len(lines) <= maxlines or s <= 28: break
        s -= 4
    for ln in lines:
        d.text((cx, y), ln.replace(NB, " ") if False else ln, font=f, fill=fill, anchor="ma")
        y += int(s * gap)
    return y

import functools
@functools.lru_cache(maxsize=32)
def _vgrad(top, bot):
    a = np.linspace(0, 1, H)[:, None, None]
    arr = (np.array(top)[None, None, :] * (1 - a) + np.array(bot)[None, None, :] * a)
    return Image.fromarray(np.repeat(arr, W, axis=1).astype("uint8"), "RGB")

def vgrad(top, bot):
    return _vgrad(tuple(top), tuple(bot)).copy()

def pill(d, cx, y, text, fill, fg=(255, 255, 255), size=34):
    f = font(size); w = int(d.textlength(text, font=f)) + 56
    d.rounded_rectangle((cx - w // 2, y, cx + w // 2, y + size + 28), radius=(size + 28) // 2, fill=fill)
    d.text((cx, y + 14), text, font=f, fill=fg, anchor="ma")

def brand_tag(d):
    """Small 'Tiny French' tag above the artwork. The big wordmark sat at y=230-300, right on top of shop signs
    (BOULANGERIE starts at y=250), so story scenes use this compact pill in the top margin instead."""
    f = font(38); w = int(d.textlength("Tiny French", font=f)) + 64
    d.rounded_rectangle((W // 2 - w // 2, 128, W // 2 + w // 2, 196), radius=34, fill=(255, 255, 255, 248))
    d.text((W // 2, 162), "Tiny French", font=f, fill=NAVY, anchor="mm")

def wordmark(d, y=SAFE_TOP + 10):
    d.text((W // 2, y), "Tiny French", font=font(56), fill=NAVY, anchor="ma")
    d.polygon([(W // 2 + 210, y + 8), (W // 2 + 220, y + 32), (W // 2 + 246, y + 34), (W // 2 + 226, y + 50), (W // 2 + 234, y + 76),
               (W // 2 + 210, y + 60), (W // 2 + 186, y + 76), (W // 2 + 194, y + 50), (W // 2 + 174, y + 34), (W // 2 + 200, y + 32)], fill=BLUSH)

# ---- frames ----
def f_title(seg, t, meta):
    img = vgrad(LAVENDER, BLUSH); d = ImageDraw.Draw(img); wordmark(d, 520)
    y = block(d, W // 2, 760, meta["title"], 78, NAVY, 900, maxlines=4)
    pill(d, W // 2, y + 30, f"Épisode {meta.get('episode', '1')}", NAVY)
    d.text((W // 2, SAFE_BOTTOM - 130), "Small steps. Big dreams.", font=font(40, False), fill=NAVY, anchor="ma")
    return img

def f_story(seg, t, meta):
    img = SC.background(seg["place"]); stage = seg["stage"]; d = ImageDraw.Draw(img, "RGBA"); brand_tag(d)
    pill(d, W // 2, 330, seg["place"].title(), (255, 255, 255, 190), fg=NAVY, size=30)
    poses = {n: stage.pose(n, t) for n in acting.NAMES}
    for n in sorted(acting.NAMES, key=lambda k: poses[k]["lane"]):
        P = poses[n]
        if not P["vis"]: continue
        sp = n == seg.get("speaker")
        spr = rig.draw(n, dict(P, mouth=seg["mouth"](t) if sp else 0.0, t=t))
        sc = SC.scale_of(seg["place"]) * (1.0 + P["lane"] * 0.0009)
        spr = spr.resize((int(spr.width * sc), int(spr.height * sc)), Image.BILINEAR)
        feet = SC.floor_of(seg["place"]) + P["lane"] * 0.55
        d.ellipse((P["x"] - 150 * sc, feet - 16, P["x"] + 150 * sc, feet + 16), fill=(40, 44, 78, 58))   # contact shadow
        img.paste(spr, (int(P["x"] - rig.CX * sc), int(feet - rig.FY * sc)), spr)
    if seg.get("speaker"):
        d = ImageDraw.Draw(img, "RGBA")
        d.rounded_rectangle((60, 1290, W - 60, SAFE_BOTTOM + 20), radius=48, fill=(255, 255, 255, 235))
        pill(d, W // 2, 1262, seg["speaker"], CHARS[seg["speaker"]]["jacket"], size=32)
        y = block(d, W // 2, 1340, seg["fr"], 60, NAVY, 900, maxlines=3)
        block(d, W // 2, y + 10, seg["en"], 40, MUTED, 900, bold=False, maxlines=2)
    return img

def card_frame(tag, tag_color):
    img = vgrad(CREAM, (240, 232, 252)); d = ImageDraw.Draw(img); wordmark(d)
    d.rounded_rectangle((60, 380, W - 60, SAFE_BOTTOM), radius=56, fill=(255, 255, 255)); pill(d, W // 2, 350, tag, tag_color)
    return img, d

def f_vocab(seg, t, meta):
    img, d = card_frame("Vocabulaire · Vocabulary", (120, 150, 220))
    y = block(d, W // 2, 470, seg["term"], 104, NAVY, 880, maxlines=2)
    y = block(d, W // 2, y + 24, "means", 42, MUTED, 880, bold=False)
    y = block(d, W // 2, y + 4, seg["meaning"], 78, (74, 112, 200), 880, maxlines=2)
    if seg["example"]:
        fr, en = seg["example"]
        d.line((200, y + 60, W - 200, y + 60), fill=(225, 220, 240), width=4)
        y = block(d, W // 2, y + 100, fr, 46, NAVY, 860, maxlines=3)
        if en: block(d, W // 2, y + 10, en, 36, MUTED, 860, bold=False, maxlines=3)
    return img

def f_grammar(seg, t, meta):
    img, d = card_frame("Grammaire · Grammar", (92, 168, 120))
    y = block(d, W // 2, 520, seg["pattern"], 84, NAVY, 880, maxlines=2)
    y = block(d, W // 2, y + 20, seg["meaning"], 50, (92, 168, 120), 880, maxlines=2)
    d.line((200, y + 50, W - 200, y + 50), fill=(225, 240, 228), width=4); y += 90
    for fr, en in seg["examples"][:2]:
        y = block(d, W // 2, y, fr, 46, NAVY, 860, maxlines=2)
        if en: y = block(d, W // 2, y + 4, en, 34, MUTED, 860, bold=False, maxlines=2)
        y += 40
    return img

def f_quiz(seg, t, meta):
    img, d = card_frame("Quiz", (240, 150, 100)); q = seg["quiz"]
    y = block(d, W // 2, 480, q.question, 54, NAVY, 880, maxlines=4) + 30
    for L, txt in sorted(q.options.items()):
        win = seg["reveal"] and L == q.answer
        col = (150, 205, 165) if win else ((244, 240, 250) if not seg["reveal"] else (250, 246, 252))
        d.rounded_rectangle((100, y, W - 100, y + 120), radius=36, fill=col)
        d.text((150, y + 60), L, font=font(54), fill=NAVY, anchor="lm")
        d.text((230, y + 60), txt, font=font(42 if len(txt) < 34 else 34, False), fill=NAVY if not seg["reveal"] or win else (150, 150, 170), anchor="lm")
        y += 150
    if seg["reveal"]:
        block(d, W // 2, y + 20, q.explanation, 38, MUTED, 860, bold=False, maxlines=4)
    else:
        frac = max(0.0, min(1.0, (t - seg["t0"] - seg["think_from"]) / max(0.1, seg["t1"] - seg["t0"] - seg["think_from"])))
        d.rounded_rectangle((140, y + 30, W - 140, y + 54), radius=12, fill=(235, 230, 245))
        d.rounded_rectangle((140, y + 30, 140 + int((W - 280) * (1 - frac)), y + 54), radius=12, fill=(240, 150, 100))
    return img

def f_outro(seg, t, meta):
    img = vgrad(BLUSH, LAVENDER); d = ImageDraw.Draw(img); wordmark(d, 700)
    block(d, W // 2, 860, "À demain ! See you tomorrow!", 60, NAVY, 880, maxlines=2)
    d.text((W // 2, SAFE_BOTTOM - 130), "Small steps. Big dreams.", font=font(40, False), fill=NAVY, anchor="ma")
    return img

DRAW = {"title": f_title, "story": f_story, "vocab": f_vocab, "grammar": f_grammar, "quiz": f_quiz, "outro": f_outro}

# ---- timeline ----
def envelope(x):
    n = int(SR / FPS); m = len(x) // n
    e = np.sqrt(np.mean(x[:m * n].reshape(m, n) ** 2, axis=1)) if m else np.zeros(1)
    return e

def build(script, tmp, dummy=False, sections=("story", "vocab", "grammar", "quiz"), max_quiz=1):
    segs, mix, cues, skipped = [], [], [], 0
    cnt = [0]
    def speak(text, voice, rate=None):
        cnt[0] += 1; p = os.path.join(tmp, f"a{cnt[0]:03}.wav"); synth(text, voice, p, dummy, rate); return read_wav(p)
    def place(t0, x): mix.append((t0, x))
    t = 0.0
    segs.append(dict(kind="title", t0=0, t1=2.6)); t = 2.6
    stage = None
    if "story" in sections:
        voices = {}
        for ev in script.story:
            if isinstance(ev, Say): voices[id(ev)] = speak(ev.fr, CHARS[ev.speaker]["voice"])
        stage, items, tend = acting.play(script, lambda ev: len(voices[id(ev)]) / SR, t0=t)
        for it in items:
            if it[0] == "act":
                segs.append(dict(kind="story", t0=it[1], t1=it[2], place=it[3], speaker=None, stage=stage))
            elif it[0] == "say":
                ev = it[3]; x = voices[id(ev)]; dur = len(x) / SR; env = envelope(x)
                def mouth(tt, env=env, t0=it[1] + 0.15):
                    i = int((tt - t0) * FPS); return float(min(1.0, env[i] * 7)) if 0 <= i < len(env) else 0.0
                segs.append(dict(kind="story", t0=it[1], t1=it[2], speaker=ev.speaker, fr=ev.fr, en=ev.en, place=it[4], mouth=mouth, stage=stage))
                place(it[1] + 0.15, x); cues.append((it[1] + 0.15, it[1] + 0.15 + dur + 0.25, ev.fr, ev.en))
        t = tend
    if "vocab" in sections:
        for v in script.vocab:
            # French word -> English "means ..." -> French word again, slowly (the viewer hears AND sees the meaning)
            x = speak(v.term, CHARS["Marinette"]["voice"]); parts = [(0.3, x)]; d = 0.3 + len(x) / SR + 0.45
            m = speak("means " + v.meaning, EN_VOICE, "+0%"); parts.append((d, m)); d += len(m) / SR + 0.45
            x2 = speak(v.term, CHARS["Marinette"]["voice"], "-25%"); parts.append((d, x2)); d += len(x2) / SR + 0.6
            ex = v.examples[0] if v.examples else None
            if ex:
                y = speak(ex[0], CHARS["Adrien"]["voice"]); parts.append((d, y)); d += len(y) / SR + 0.8
            for off, a in parts: place(t + off, a)
            segs.append(dict(kind="vocab", t0=t, t1=t + max(d, 3.2), term=v.term, meaning=v.meaning, example=ex))
            cues.append((t + 0.3, t + 0.3 + len(x) / SR + 0.2, v.term, v.meaning)); t += max(d, 3.2)
    if "grammar" in sections:
        for g in script.grammar:
            d = 0.6; parts = []
            for i, (fr, en) in enumerate(g.examples[:2]):
                a = speak(fr, CHARS["Marinette" if i == 0 else "Adrien"]["voice"]); parts.append((d, a)); d += len(a) / SR + 0.9
            for off, a in parts: place(t + off, a)
            segs.append(dict(kind="grammar", t0=t, t1=t + max(d + 1.2, 6.0), pattern=g.pattern, meaning=g.meaning, examples=g.examples)); t += max(d + 1.2, 6.0)
    if "quiz" in sections:
        for q in script.quiz[:max_quiz]:
            a = speak(q.question, NARRATOR_VOICE); d1 = 0.4 + len(a) / SR + 0.5; place(t + 0.4, a)
            segs.append(dict(kind="quiz", t0=t, t1=t + d1 + 4.0, quiz=q, reveal=False, think_from=d1)); t += d1 + 4.0
            b = speak(f"The answer is {q.answer}. {q.explanation}", NARRATOR_VOICE); d2 = 0.3 + len(b) / SR + 1.0; place(t + 0.3, b)
            segs.append(dict(kind="quiz", t0=t, t1=t + d2, quiz=q, reveal=True, think_from=0)); t += d2
    segs.append(dict(kind="outro", t0=t, t1=t + 2.4)); t += 2.4
    return segs, mix, cues, skipped, t

def render(script, outdir, stem, dummy=False, preview=None, sections=("story", "vocab", "grammar", "quiz"), max_quiz=1):
    os.makedirs(outdir, exist_ok=True)
    tmp = os.path.join(outdir, ".tmp"); os.makedirs(tmp, exist_ok=True)
    segs, mix, cues, skipped, total = build(script, tmp, dummy, sections, max_quiz)
    audio = np.zeros(int(total * SR) + SR, dtype=np.float32)
    for t0, x in mix:
        i = int(t0 * SR); audio[i:i + len(x)] += x[:len(audio) - i]
    wav = os.path.join(tmp, "mix.wav"); write_wav(wav, np.clip(audio, -1, 1))
    write_srt(os.path.join(outdir, stem + ".srt"), cues)
    last = [None, None]
    STATIC = ("title", "vocab", "grammar", "outro")
    def frame(t):
        for s in segs:
            if s["t0"] <= t < s["t1"]:
                if s["kind"] in STATIC or (s["kind"] == "quiz" and s["reveal"]):
                    if last[0] is not s: last[0] = s; last[1] = DRAW[s["kind"]](s, t, script.meta)
                    return last[1]
                return DRAW[s["kind"]](s, t, script.meta)
        return frame(segs[-1]["t0"])
    if preview:
        os.makedirs(preview, exist_ok=True)
        for i, s in enumerate(segs):
            frame((s["t0"] + s["t1"]) / 2 + 0.05).save(os.path.join(preview, f"{i:02}-{s['kind']}.png"))
    mp4 = os.path.join(outdir, stem + ".mp4"); n = int(total * FPS)
    X264 = (["-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency", "-crf", "20", "-threads", "1"] if os.environ.get("TF_LOWMEM") == "1"
            else ["-c:v", "libx264", "-preset", "veryfast", "-crf", "21"])
    logf = open(os.path.join(tmp, "ffmpeg.log"), "w")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "warning", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-i", wav, *X264, "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                          "-shortest", "-movflags", "+faststart", mp4], stdin=subprocess.PIPE, stderr=logf)
    try:
        for i in range(n):
            p.stdin.write(frame(i / FPS).tobytes())
        p.stdin.close()
    except BrokenPipeError:
        p.wait(); sys.exit("ERROR: ffmpeg stopped early (rc=%s):\n%s" % (p.returncode, open(os.path.join(tmp, "ffmpeg.log")).read()[-1500:]))
    if p.wait() != 0: sys.exit("ERROR: ffmpeg failed:\n" + open(os.path.join(tmp, "ffmpeg.log")).read()[-1500:])
    info = dict(title=script.meta["title"], width=W, height=H, fps=FPS, seconds=round(total, 2), sections=list(sections), directions_not_animated=skipped)
    json.dump(info, open(os.path.join(outdir, stem + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return info
