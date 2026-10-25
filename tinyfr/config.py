"""Tiny French - shared settings (vertical Reels format)."""
import os
W, H, FPS, SR = 1080, 1920, 24, 24000
# Instagram overlays the top ~220px and bottom ~380px of a Reel: keep text inside this band.
SAFE_TOP, SAFE_BOTTOM = 220, H - 380
NAVY = (38, 48, 74); LAVENDER = (185, 167, 245); BLUSH = (246, 182, 205)
SKY = (169, 208, 245); CREAM = (255, 245, 232); GREEN = (184, 214, 193)
MUTED = (96, 104, 130)
CHARS = {
    "Marinette": dict(voice="fr-FR-DeniseNeural", hair=(50, 68, 122), hl=(92, 112, 170), skin=(253, 227, 203), jacket=(84, 74, 80), top=(242, 234, 234), edge=(62, 54, 60),
                      trouser=(60, 66, 104), shoe=(245, 240, 236), iris=(108, 56, 70), strap=(150, 96, 78), bag=(246, 214, 196), ribbon=(206, 54, 64)),
    "Adrien": dict(voice="fr-FR-HenriNeural", hair=(247, 208, 120), hl=(255, 238, 176), hair_d=(226, 170, 84), brow=(206, 154, 88), skin=(253, 227, 203), jacket=(244, 238, 238),
                   top=(42, 36, 42), edge=(224, 212, 214), trouser=(78, 92, 128), shoe=(255, 255, 255), iris=(108, 56, 70), strap=(120, 84, 56), bag=(168, 120, 80)),
}
NARRATOR_VOICE = "en-US-AriaNeural"   # English quiz narration
VOICE_RATE = os.environ.get("TF_VOICE_RATE", "-8%")  # slightly slow for beginners
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
FONT_REG_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]
