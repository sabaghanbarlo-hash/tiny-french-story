"""Practice-style reel generator for Tiny French (side generator; the original small.py system is unchanged).

Format (~20 s): big hook -> 3 short lines -> "Your turn! Say it out loud!" with a 3-2-1 countdown ->
the first speaker says the key phrase -> "Save this / send it to a study buddy". No vocab recap.

Usage:  python practice_reel.py practice/01-introduce-yourself.txt -o output/practice
Story files use the normal Small format; the FIRST `vocab:` line is the practice phrase.
"""
import argparse, math, os, re, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import small as sm  # noqa: E402
from sprites import sprite, CHARS  # noqa: E402

W, H, FPS, SR = sm.W, sm.H, sm.FPS, sm.SR
HOOK = 2.0


def silence(sec):
    return np.zeros(int(sec * SR), np.float32)


def ring(n, f):
    s = 260; im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((6, 6, s - 6, s - 6), fill=(255, 253, 250, 240))
    d.arc((14, 14, s - 14, s - 14), -90, -90 + 360 * f, fill=sm.BRAND, width=22)
    d.text((s / 2, s / 2 + 4), str(n), font=sm.font(130), fill=sm.BRAND, anchor="mm")
    return im


def build(text, rate, dummy, tmp):
    meta, lines, vocab = sm.parse_story(text)
    if not vocab:
        raise sm.ScriptProblem("Add a 'vocab: French | pronunciation | English' line: it is the phrase the viewer practises.")
    key = vocab[0]
    cast = [n.strip() for n in meta.get("cast", "").split(",") if n.strip()] or list(dict.fromkeys(ln["speaker"] for ln in lines))
    for idx, name in enumerate(dict.fromkeys(cast + [ln["speaker"] for ln in lines])):
        if name not in CHARS:
            base = CHARS["Adrien"] if idx % 2 == 0 else CHARS["Marinette"]
            CHARS[name] = dict(base)
    meta["scene"] = sm.pick_scene(meta, lines)
    if len(cast) == 1:
        cast.append("Adrien" if cast[0] != "Adrien" else "Marinette")
    voice = lambda nm: CHARS[nm]["voice"]
    chunks, t = [silence(0.15)], 0.15
    for i, ln in enumerate(lines):
        wav = os.path.join(tmp, f"l{i}.wav"); sm.synth(ln["fr"], voice(ln["speaker"]), wav, rate, dummy)
        x = sm.read_wav(wav); ln["start"], ln["end"] = t, t + len(x) / SR
        chunks += [x, silence(0.25)]; t = ln["end"] + 0.25
    talk = list(lines)
    aria = "en-US-AriaNeural"
    wav = os.path.join(tmp, "turn.wav"); sm.synth("Your turn! Say it out loud!", aria, wav, "+5%", dummy, lang="en")
    x = sm.read_wav(wav); turn0 = t; chunks += [x, silence(0.3)]; t += len(x) / SR + 0.3
    cd0 = t; chunks.append(silence(3.0)); t += 3.0
    wav = os.path.join(tmp, "key.wav"); sm.synth(key["fr"], voice(cast[0]), wav, "-20%", dummy)
    x = sm.read_wav(wav); key0 = t; talk.append(dict(speaker=cast[0], start=t, end=t + len(x) / SR)); chunks += [x, silence(0.3)]; t += len(x) / SR + 0.3
    wav = os.path.join(tmp, "end.wav"); sm.synth("Perfect! Save this, and send it to a study buddy.", aria, wav, "+5%", dummy, lang="en")
    x = sm.read_wav(wav); end0 = t; chunks += [x, silence(0.6)]; t += len(x) / SR + 0.6
    audio = np.concatenate(chunks); audio = audio / max(0.01, np.abs(audio).max()) * 0.9
    n = int(t * FPS); mouth = sm.mouth_levels(audio, n)
    bg, fg = sm.make_scene(meta["scene"], meta)
    cards = [sm.line_card(l) for l in lines]
    pt = [(key["fr"], sm.font(76), (46, 48, 60), 100)]
    if key["pron"]:
        pt.append((key["pron"], sm.font(44, False), (128, 152, 204), 62))
    pt.append((key["en"], sm.font(46, False), (84, 86, 96), 64))
    turn_card = sm.card_image("Your turn!", sm.BRAND, pt, min_h=420)
    done_card = sm.card_image("Parfait!", (79, 154, 110), pt, min_h=420)
    cta_card = sm.card_image("Tiny French", sm.BRAND, [("Save this for later", sm.font(60), (46, 48, 60), 90), ("Send it to a study buddy", sm.font(44, False), (118, 122, 136), 70)], min_h=380)
    banner = sm.hook_banner(meta, "Tiny French")
    pills = {(nm, a): sm.pill(nm, CHARS[nm]["accent"] if a else (226, 214, 206), (255, 255, 255) if a else (130, 112, 108)) for nm in cast for a in (0, 1)}

    def frame(i):
        tt = i / FPS; fr = bg.copy()
        cur = next((k for k, l in enumerate(talk) if l["start"] - 0.02 <= tt <= l["end"] + 0.1), None)
        for idx, nm in enumerate(cast):
            x = 16 if idx == 0 else 560
            sp = cur is not None and talk[cur]["speaker"] == nm
            bob = 5 * abs(math.sin(tt * 7)) if sp and mouth[i] else 2 * math.sin(tt * 2 + (0 if nm == cast[0] else 1.7))
            blink = ((i + (0 if nm == cast[0] else 41)) % 97) < 4
            s = sprite(nm, int(mouth[i]) if sp else 0, blink)
            fr.paste(s, (x, int(sm.CHAR_Y - bob)), s)
            p = pills[(nm, int(sp))]; fr.paste(p, (x + s.width // 2 - p.width // 2, 322), p)
        fr.paste(fg, (0, sm.TABLE_TOP - 55), fg)
        if tt >= end0: card, t0 = cta_card, end0
        elif tt >= key0: card, t0 = done_card, key0
        elif tt >= turn0: card, t0 = turn_card, turn0
        else:
            k = max((k for k, l in enumerate(lines) if tt >= l["start"] - 0.02), default=0); card, t0 = cards[k], lines[k]["start"]
        f = max(0, min(1, (tt - t0) / 0.18)); dy = int(30 * (1 - f))
        if f < 1: card = card.copy(); card.putalpha(card.getchannel("A").point(lambda v: int(v * f)))
        fr.paste(card, (20, sm.CARD_Y - 40 + dy), card)
        if cd0 <= tt < cd0 + 3.0:
            u = tt - cd0; r = ring(3 - int(u), 1 - (u - int(u)))
            fr.paste(r, ((W - r.width) // 2, sm.CARD_Y + 470), r)
        if tt < HOOK:
            a = min(1.0, tt / 0.12, (HOOK - tt) / 0.3)
            if a > 0:
                b = banner if a >= 1 else banner.copy()
                if a < 1: b.putalpha(b.getchannel("A").point(lambda v: int(v * a)))
                fr.paste(b, (40, 130), b)
        return fr.convert("RGB")

    return meta, lines, audio, n, frame


def main():
    ap = argparse.ArgumentParser(description="Tiny French practice-style reel")
    ap.add_argument("script"); ap.add_argument("-o", "--out", default="output/practice")
    ap.add_argument("--rate", default="-10%"); ap.add_argument("--dummy-audio", action="store_true", help="TEST ONLY: tones instead of voices")
    a = ap.parse_args()
    text = open(a.script, encoding="utf-8").read()
    stem = os.path.splitext(os.path.basename(a.script))[0]; os.makedirs(a.out, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            meta, lines, audio, n, frame = build(text, a.rate, a.dummy_audio, tmp)
            wav = os.path.join(tmp, "final.wav"); sm.write_wav(wav, audio)
            mp4 = os.path.join(a.out, stem + ".mp4")
            p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                                  "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                                  "-movflags", "+faststart", "-t", f"{n / FPS:.2f}", mp4], stdin=subprocess.PIPE)
            for i in range(n):
                p.stdin.write(frame(i).tobytes())
            p.stdin.close()
            if p.wait() != 0:
                sys.exit("::error::FFmpeg failed while encoding the video.")
    except sm.ScriptProblem as e:
        print("::error title=Script problem::" + str(e)); sys.exit(1)
    print(f"Wrote {mp4} ({n / FPS:.1f}s)")


if __name__ == "__main__":
    main()
