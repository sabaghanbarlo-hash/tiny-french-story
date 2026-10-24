#!/usr/bin/env python3
"""Cut Adrien and Marinette out of the reference picture.

Usage: python extract_sprites.py [picture] [assets/sprites]
Without arguments it uses the first picture found in assets/reference/ (any name, .png/.jpg/.jpeg).
Needs: pip install opencv-python-headless
"""
import glob, sys
from charart import extract

if __name__ == "__main__":
    found = sorted(glob.glob("assets/reference/*.png") + glob.glob("assets/reference/*.jpg") + glob.glob("assets/reference/*.jpeg"))
    ref = sys.argv[1] if len(sys.argv) > 1 else (found[0] if found else None)
    if not ref:
        sys.exit("No picture found. Put the reference picture in assets/reference/.")
    out = sys.argv[2] if len(sys.argv) > 2 else "assets/sprites"
    meta = extract(ref, out)
    print("Wrote sprites for:", ", ".join(meta), "->", out)
