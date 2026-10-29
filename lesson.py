#!/usr/bin/env python3
"""python lesson.py lessons/01-bakery.txt -o output   (vertical 1080x1920 Reel + SRT)"""
import argparse, os, sys
from tinyfr.parser import ScriptError
from tinyfr.autodirect import parse_any
from tinyfr.render import render
from tinyfr import acting
from tinyfr.meta import write_caption
from tinyfr.thumb import make_cover

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script"); ap.add_argument("-o", "--out", default="output")
    ap.add_argument("--preview", help="folder for still frames"); ap.add_argument("--dummy-audio", action="store_true", help="TEST ONLY: tones instead of voices")
    ap.add_argument("--sections", default="story,vocab,grammar,quiz"); ap.add_argument("--max-quiz", type=int, default=1)
    a = ap.parse_args()
    try:
        script = parse_any(open(a.script, encoding="utf-8").read())
    except ScriptError as e:
        sys.exit(f"Script error: {e}")
    try:
        acting.check(script)
    except ScriptError as e:
        sys.exit(f"Script error: {e}")
    if a.dummy_audio:
        print("WARNING: --dummy-audio is for tests only; the video will not have French speech.", file=sys.stderr)
    stem = os.path.splitext(os.path.basename(a.script))[0]
    info = render(script, a.out, stem, a.dummy_audio, a.preview, tuple(a.sections.split(",")), a.max_quiz)
    write_caption(script, os.path.join(a.out, stem + ".caption.txt")); make_cover(script, os.path.join(a.out, stem + ".cover.png"))
    print(info)

if __name__ == "__main__":
    main()
