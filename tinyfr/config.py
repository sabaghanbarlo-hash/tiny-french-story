"""Tiny French - shared settings (vertical Reels format)."""
import os
W, H, FPS, SR = 1080, 1920, 24, 24000
# Instagram overlays the top ~220px and bottom ~380px of a Reel: keep text inside this band.
SAFE_TOP, SAFE_BOTTOM = 220, H - 380
NAVY = (38, 48, 74); LAVENDER = (185, 167, 245); BLUSH = (246, 182, 205)
SKY = (169, 208, 245); CREAM = (255, 245, 232); GREEN = (184, 214, 193)
MUTED = (96, 104, 130)
CHARS = {
    "Camille": dict(voice="fr-FR-DeniseNeural", hair=(30, 40, 90), hl=(150, 98, 110), skin=(250, 220, 200), jacket=(238, 150, 176), top=(255, 245, 232), edge=(214, 120, 150),
                    trouser=(52, 56, 112), shoe=(245, 240, 236), iris=(120, 78, 48), strap=(150, 96, 78), bag=(246, 214, 196), ribbon=(214, 66, 88)),
    "Julien": dict(voice="fr-FR-HenriNeural", hair=(240, 200, 96), hl=(255, 230, 150), brow=(176, 128, 56), skin=(244, 208, 180), jacket=(48, 72, 132), top=(250, 246, 238), edge=(198, 58, 70),
                   trouser=(78, 92, 128), shoe=(255, 255, 255), iris=(88, 128, 190), strap=(120, 84, 56), bag=(168, 120, 80), scarf=(205, 60, 72)),
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
