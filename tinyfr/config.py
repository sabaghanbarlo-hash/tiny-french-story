"""Tiny French - shared settings (vertical Reels format)."""
import os
W, H, FPS, SR = 1080, 1920, 24, 24000
# Instagram overlays the top ~220px and bottom ~380px of a Reel: keep text inside this band.
SAFE_TOP, SAFE_BOTTOM = 220, H - 380
# Characters are drawn 840x1000 (body ~315px wide). At 1.0 they tower over the scene props and fill the screen,
# so every story scene draws them at CHAR_SCALE (per-scene overrides: scenes.SCENE_TUNING).
CHAR_SCALE = 0.62
BODY_W = 315
NAVY = (38, 48, 74); LAVENDER = (185, 167, 245); BLUSH = (246, 182, 205)
SKY = (169, 208, 245); CREAM = (255, 245, 232); GREEN = (184, 214, 193)
MUTED = (96, 104, 130)
CHARS = {
    "Marinette": dict(voice="fr-FR-DeniseNeural", hair=(50, 68, 122), hl=(92, 112, 170), skin=(253, 227, 203), jacket=(84, 74, 80), top=(242, 234, 234), edge=(62, 54, 60),
                      trouser=(60, 66, 104), shoe=(245, 240, 236), iris=(108, 56, 70), strap=(150, 96, 78), bag=(246, 214, 196), ribbon=(206, 54, 64)),
    "Adrien": dict(voice="fr-FR-HenriNeural", hair=(247, 208, 120), hl=(255, 238, 176), hair_d=(226, 170, 84), brow=(206, 154, 88), skin=(253, 227, 203), jacket=(244, 238, 238),
                   top=(42, 36, 42), edge=(224, 212, 214), trouser=(78, 92, 128), shoe=(255, 255, 255), iris=(108, 56, 70), strap=(120, 84, 56), bag=(168, 120, 80)),
    "Alia": dict(voice="fr-FR-DeniseNeural", hair=(145, 62, 48), hl=(205, 112, 78), hair_d=(105, 42, 38), brow=(105, 42, 38), skin=(253, 227, 203), jacket=(205, 153, 54), top=(255, 239, 204), edge=(160, 111, 43), trouser=(83, 72, 78), shoe=(255, 245, 232), iris=(92, 125, 92), strap=(120, 84, 56), bag=(205, 153, 54)),
    "Nino": dict(voice="fr-FR-HenriNeural", hair=(82, 53, 39), hl=(133, 91, 65), hair_d=(58, 38, 31), brow=(58, 38, 31), skin=(253, 227, 203), jacket=(54, 151, 145), top=(226, 245, 238), edge=(37, 112, 108), trouser=(65, 75, 88), shoe=(255, 255, 255), iris=(75, 142, 105), strap=(80, 80, 70), bag=(54, 151, 145)),
    "Chloé": dict(voice="fr-FR-DeniseNeural", hair=(151, 105, 67), hl=(207, 161, 111), hair_d=(111, 74, 48), brow=(111, 74, 48), skin=(253, 227, 203), jacket=(181, 157, 224), top=(247, 240, 255), edge=(139, 119, 186), trouser=(91, 82, 112), shoe=(255, 255, 255), iris=(108, 83, 128), strap=(120, 84, 56), bag=(181, 157, 224)),
    "Lucas": dict(voice="fr-FR-HenriNeural", hair=(35, 31, 34), hl=(83, 73, 75), hair_d=(20, 18, 21), brow=(20, 18, 21), skin=(253, 227, 203), jacket=(177, 91, 57), top=(255, 225, 194), edge=(139, 63, 44), trouser=(74, 72, 82), shoe=(255, 255, 255), iris=(93, 111, 126), strap=(120, 84, 56), bag=(177, 91, 57)),
    "Cat": dict(voice="fr-FR-HenriNeural", hair=(247, 190, 82), hl=(255, 218, 135), hair_d=(220, 151, 55), brow=(220, 151, 55), skin=(253, 227, 203), jacket=(37, 31, 39), top=(37, 31, 39), edge=(66, 58, 65), trouser=(37, 31, 39), shoe=(66, 58, 65), iris=(112, 132, 82), strap=(247, 190, 82), bag=(66, 58, 65)),
    "Bugaboo": dict(voice="fr-FR-DeniseNeural", hair=(48, 61, 112), hl=(76, 91, 145), hair_d=(34, 44, 92), brow=(34, 44, 92), skin=(253, 227, 203), jacket=(218, 54, 58), top=(218, 54, 58), edge=(150, 28, 39), trouser=(38, 34, 46), shoe=(38, 38, 48), iris=(105, 75, 78), strap=(38, 38, 48), bag=(218, 54, 58)),
}
NARRATOR_VOICE = "en-US-AriaNeural"   # English quiz narration
EN_VOICE = NARRATOR_VOICE              # English "means ..." in the vocabulary section
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
