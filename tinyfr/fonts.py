import os, sys
from PIL import ImageFont
from .config import FONT_CANDIDATES, FONT_REG_CANDIDATES
_fc = {}
def font(size, bold=True):
    key = (size, bold)
    if key not in _fc:
        for p in (FONT_CANDIDATES if bold else FONT_REG_CANDIDATES):
            if os.path.exists(p):
                _fc[key] = ImageFont.truetype(p, size); break
        else:
            sys.exit("ERROR: no usable TrueType font found (install fonts-dejavu-core)")
    return _fc[key]
