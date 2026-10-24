#!/usr/bin/env python3
"""Cut Adrien and Marinette out of the reference picture.

Usage: python extract_sprites.py [assets/reference/characters.png] [assets/sprites]
Needs: pip install opencv-python-headless
"""
import sys
from charart import extract

if __name__ == "__main__":
    ref = sys.argv[1] if len(sys.argv) > 1 else "assets/reference/characters.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "assets/sprites"
    meta = extract(ref, out)
    print("Wrote sprites for:", ", ".join(meta), "->", out)
