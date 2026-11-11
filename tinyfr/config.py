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
    "Marinette": dict(voice="fr-FR-DeniseNeural", hair=(34, 34, 44), hl=(74, 76, 98), skin=(253, 227, 203), jacket=(88, 130, 182), top=(250, 244, 232), edge=(62, 98, 146),
                      trouser=(236, 228, 212), shoe=(214, 64, 70), iris=(108, 56, 70), strap=(40, 52, 92), bag=(250, 244, 232), ribbon=(206, 54, 64)),
    "Adrien": dict(voice="fr-FR-HenriNeural", hair=(120, 80, 52), hl=(160, 114, 80), hair_d=(92, 58, 36), brow=(92, 58, 36), skin=(253, 227, 203), jacket=(44, 58, 104),
                   top=(250, 248, 244), edge=(30, 42, 80), trouser=(196, 160, 112), shoe=(110, 70, 48), iris=(108, 56, 70), strap=(120, 80, 52), bag=(150, 100, 64)),
    "Alia": dict(voice="fr-FR-DeniseNeural", hair=(145, 62, 48), hl=(205, 112, 78), hair_d=(105, 42, 38), brow=(105, 42, 38), skin=(253, 227, 203), jacket=(205, 153, 54), top=(255, 239, 204), edge=(160, 111, 43), trouser=(83, 72, 78), shoe=(255, 245, 232), iris=(92, 125, 92), strap=(120, 84, 56), bag=(205, 153, 54)),
    "Nino": dict(voice="fr-FR-HenriNeural", hair=(82, 53, 39), hl=(133, 91, 65), hair_d=(58, 38, 31), brow=(58, 38, 31), skin=(253, 227, 203), jacket=(54, 151, 145), top=(226, 245, 238), edge=(37, 112, 108), trouser=(65, 75, 88), shoe=(255, 255, 255), iris=(75, 142, 105), strap=(80, 80, 70), bag=(54, 151, 145)),
    "Chloé": dict(voice="fr-FR-DeniseNeural", hair=(151, 105, 67), hl=(207, 161, 111), hair_d=(111, 74, 48), brow=(111, 74, 48), skin=(253, 227, 203), jacket=(181, 157, 224), top=(247, 240, 255), edge=(139, 119, 186), trouser=(91, 82, 112), shoe=(255, 255, 255), iris=(108, 83, 128), strap=(120, 84, 56), bag=(181, 157, 224)),
    "Lucas": dict(voice="fr-FR-HenriNeural", hair=(35, 31, 34), hl=(83, 73, 75), hair_d=(20, 18, 21), brow=(20, 18, 21), skin=(253, 227, 203), jacket=(177, 91, 57), top=(255, 225, 194), edge=(139, 63, 44), trouser=(74, 72, 82), shoe=(255, 255, 255), iris=(93, 111, 126), strap=(120, 84, 56), bag=(177, 91, 57)),
    "Cat": dict(voice="fr-FR-HenriNeural", hair=(26, 26, 36), hl=(70, 70, 90), hair_d=(16, 16, 24), brow=(96, 220, 140), skin=(253, 227, 203), jacket=(34, 34, 48), top=(48, 48, 66), edge=(20, 20, 30),
                trouser=(34, 34, 48), shoe=(22, 22, 30), iris=(80, 190, 110), strap=(96, 220, 140), bag=(34, 34, 48), glove=(96, 220, 140), cape=(34, 34, 48), cape2=(96, 220, 140), accent=(96, 220, 140), emblem_bg=(26, 26, 36)),
    "Bugaboo": dict(voice="fr-FR-DeniseNeural", hair=(92, 54, 38), hl=(140, 94, 70), hair_d=(66, 38, 26), brow=(66, 38, 26), skin=(253, 227, 203), jacket=(48, 96, 206), top=(66, 118, 226), edge=(30, 66, 160),
                    trouser=(48, 96, 206), shoe=(206, 40, 56), iris=(105, 75, 78), strap=(255, 205, 60), bag=(255, 205, 60), glove=(206, 40, 56), cape=(206, 40, 56), cape2=(150, 24, 40), accent=(255, 205, 60), emblem_bg=(206, 40, 56)),
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
