"""Drawn characters for Tiny French: Adrien and Marinette (chibi, soft flat colours), animated by code."""
import functools, math
from PIL import Image, ImageDraw, ImageFilter

CHAR_SCALE = 0.9
SKIN = (253, 227, 203)
SKIN_SH = (240, 205, 178)
INK = (92, 52, 56)
CHARS = {
    "Adrien": dict(voice="fr-FR-HenriNeural", accent=(95, 158, 134), x=16),
    "Marinette": dict(voice="fr-FR-DeniseNeural", accent=(228, 140, 152), x=560),
    "Camille": dict(voice="fr-FR-DeniseNeural", accent=(205, 153, 54), x=16),
    "Théo": dict(voice="fr-FR-HenriNeural", accent=(54, 151, 145), x=560),
    "Chloé": dict(voice="fr-FR-DeniseNeural", accent=(181, 157, 224), x=16),
    "Lucas": dict(voice="fr-FR-HenriNeural", accent=(177, 91, 57), x=560),
    "Félix": dict(voice="fr-FR-HenriNeural", accent=(247, 190, 82), x=16),
    "Zoé": dict(voice="fr-FR-DeniseNeural", accent=(224, 45, 52), x=560),
}


def _bez(p0, p1, p2, n=14):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in [i / n for i in range(n + 1)]]


def lock_pts(root, ctrl, tip, width, n=14):
    """Pointed hair lock along a curve: thick in the middle, sharp at the tip."""
    c = _bez(root, ctrl, tip, n)
    left, right = [], []
    for i, (x, y) in enumerate(c):
        a = c[min(i + 1, n)]; b = c[max(i - 1, 0)]
        dx, dy = a[0] - b[0], a[1] - b[1]; L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        w = width * math.sin(math.pi * (0.12 + 0.88 * i / n) ** 0.9) * (1 - 0.15 * i / n) / 2
        if i == n:
            w = 0
        left.append((x + nx * w, y + ny * w)); right.append((x - nx * w, y - ny * w))
    return left + right[::-1]


def _eyes(d, P, S, blink, lash):
    for ex in (214, 346):
        if blink:
            d.arc(P(ex - 30, 346, ex + 30, 392), 200, 340, fill=(60, 34, 46), width=int(7 * S))
            if lash:
                side = -1 if ex < 280 else 1
                d.line(P(ex + side * 30, 372, ex + side * 42, 362), fill=(52, 28, 40), width=int(5 * S))
            continue
        d.ellipse(P(ex - 27, 318, ex + 27, 396), fill=(58, 30, 46))
        d.ellipse(P(ex - 20, 368, ex + 20, 394), fill=(108, 56, 70))
        d.ellipse(P(ex - 17, 328, ex + 4, 354), fill=(255, 255, 255))
        d.ellipse(P(ex + 6, 368, ex + 17, 380), fill=(255, 255, 255))
        d.arc(P(ex - 31, 312, ex + 31, 378), 195, 345, fill=(52, 28, 40), width=int(7 * S))
        if lash:
            side = -1 if ex < 280 else 1
            d.line(P(ex + side * 28, 344, ex + side * 44, 330), fill=(52, 28, 40), width=int(5 * S))


def _mouth(d, P, S, mouth):
    if mouth == 0:
        d.arc(P(262, 410, 298, 436), 15, 165, fill=INK, width=int(5 * S))
    elif mouth == 1:
        d.ellipse(P(268, 414, 292, 438), fill=(128, 48, 62))
    else:
        d.ellipse(P(260, 410, 300, 446), fill=(128, 48, 62)); d.ellipse(P(268, 430, 292, 444), fill=(238, 128, 140))


def _smooth(layer, S, r=5, thr=120):
    a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(r * S)).point(lambda v: 255 if v > thr else 0)
    layer.putalpha(a.filter(ImageFilter.GaussianBlur(0.8 * S)))
    return layer


@functools.lru_cache(None)
def _sprite_base(name, mouth, blink):
    S = 2 * CHAR_SCALE
    w, h = int(560 * S), int(760 * S)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    P = lambda *v: [int(x * S) for x in v]
    PP = lambda pts: [(x * S, y * S) for x, y in pts]
    ell = lambda box, fill, dd=None: (dd or d).ellipse(P(*box), fill=fill)
    poly = lambda pts, fill, dd=None: (dd or d).polygon(PP(pts), fill=fill)

    def layer(draw_fn, color, r=5):
        L = Image.new("RGBA", (w, h), color + (0,)); dd = ImageDraw.Draw(L); draw_fn(dd)
        L = Image.composite(Image.new("RGBA", (w, h), color + (255,)), L, L.getchannel("A"))
        return _smooth(L, S, r)

    def put(L):
        nonlocal im, d
        im = Image.alpha_composite(im, L); d = ImageDraw.Draw(im)

    def line(pts, col, width):
        d.line(PP(pts), fill=col, width=int(width * S), joint="curve")

    if name == "Adrien":
        gold, gold_d, gold_l = (247, 208, 120), (226, 170, 84), (255, 238, 176)
        # hair behind the head
        def back(dd):
            ell((112, 112, 448, 440), gold, dd)
            for pts in (lock_pts((150, 250), (100, 300), (74, 372), 70), lock_pts((410, 250), (462, 290), (486, 352), 64),
                        lock_pts((262, 124), (288, 76), (338, 58), 54)):
                poly(pts, gold, dd)
        put(layer(back, gold, 4))
        # body: white open jacket, black tee with rainbow stripes
        def jacket(dd):
            poly([(112, 600), (124, 540), (160, 494), (226, 466), (334, 466), (400, 494), (436, 540), (448, 600), (452, 760), (108, 760)], (244, 238, 238), dd)
        put(layer(jacket, (244, 238, 238), 6))
        tee = [(226, 490), (334, 490), (350, 760), (210, 760)]
        poly(tee, (42, 36, 42))
        xl = lambda y: 226 - 16 * (y - 490) / 270; xr = lambda y: 334 + 16 * (y - 490) / 270
        for i, c in enumerate(((110, 176, 120), (150, 108, 190), (244, 202, 100))):
            y0 = 640 + i * 26; y1 = y0 + 18
            poly([(xl(y0), y0), (xr(y0), y0), (xr(y1), y1), (xl(y1), y1)], c)
        poly([(240, 462), (320, 462), (280, 548)], SKIN)                                   # chest V
        poly([(240, 462), (262, 470), (252, 500)], SKIN_SH)
        poly([(214, 472), (246, 462), (238, 548), (198, 520)], (232, 224, 226)); poly([(346, 472), (314, 462), (322, 548), (362, 520)], (232, 224, 226))   # collar
        line([(176, 540), (196, 640)], (226, 216, 218), 4); line([(384, 540), (364, 640)], (226, 216, 218), 4)
        ell((130, 316, 180, 396), SKIN)                                                    # left ear
        ell((136, 154, 424, 462), SKIN)                                                    # face
        # fringe: big swoop from his right to his left
        def front(dd):
            poly([(118, 262), (124, 190), (196, 126), (330, 116), (432, 184), (442, 262), (430, 226), (300, 214), (180, 226)], gold, dd)
            for root, ctrl, tip, wd in (((400, 150), (420, 215), (392, 262), 66), ((340, 140), (330, 225), (296, 276), 70),
                                        ((276, 132), (240, 215), (206, 282), 76), ((206, 140), (166, 220), (150, 310), 74),
                                        ((140, 190), (118, 240), (124, 300), 50)):
                poly(lock_pts(root, ctrl, tip, wd), gold, dd)
        put(layer(front, gold, 2))
        for root, ctrl, tip in (((390, 150), (360, 200), (330, 232)), ((300, 140), (250, 190), (214, 236)), ((236, 132), (196, 180), (168, 232)), ((330, 120), (400, 150), (428, 214))):
            line(_bez(root, ctrl, tip, 10), gold_d, 6)
        for root, ctrl, tip in (((340, 130), (300, 150), (268, 178)), ((240, 126), (212, 146), (196, 176))):
            line(_bez(root, ctrl, tip, 8), gold_l, 5)
        d.arc(P(178, 296, 244, 324), 200, 340, fill=(206, 154, 88), width=int(5 * S)); d.arc(P(316, 290, 382, 318), 200, 340, fill=(206, 154, 88), width=int(5 * S))
        _eyes(d, P, S, blink, lash=False)
    else:
        navy, navy_d, navy_l = (50, 68, 122), (34, 46, 92), (92, 112, 170)
        def back(dd):
            ell((106, 106, 454, 440), navy, dd)
            poly(lock_pts((130, 250), (112, 360), (140, 470), 80), navy, dd); poly(lock_pts((430, 250), (448, 360), (420, 470), 80), navy, dd)
        put(layer(back, navy, 5))
        # body: charcoal jacket over white floral top
        def jacket(dd):
            poly([(150, 610), (160, 548), (186, 498), (240, 466), (320, 466), (374, 498), (400, 548), (410, 610), (414, 760), (146, 760)], (84, 74, 80), dd)
        put(layer(jacket, (84, 74, 80), 6))
        poly([(236, 474), (324, 474), (338, 760), (222, 760)], (242, 234, 234))
        ell((246, 446, 314, 520), SKIN)                                                    # neck / scoop neckline
        poly([(244, 462), (316, 462), (306, 500), (254, 500)], SKIN)
        poly([(226, 468), (252, 466), (264, 560), (240, 640), (212, 540)], (62, 54, 60)); poly([(334, 468), (308, 466), (296, 560), (320, 640), (348, 540)], (62, 54, 60))
        d.arc(P(244, 480, 316, 560), 20, 160, fill=(120, 110, 114), width=int(3 * S))
        for fx, fy in ((262, 640), (296, 660), (270, 690)):
            for ang in range(5):
                ax, ay = fx + 10 * math.cos(ang * 1.2566), fy + 10 * math.sin(ang * 1.2566)
                ell((ax - 7, ay - 7, ax + 7, ay + 7), (238, 150, 170))
            ell((fx - 4, fy - 4, fx + 4, fy + 4), (252, 220, 120))
        for lx, ly, rot in ((244, 668, 1), (300, 636, -1)):
            poly([(lx, ly), (lx + 16 * rot, ly - 8), (lx + 22 * rot, ly + 6)], (66, 80, 74))
        ell((136, 154, 424, 462), SKIN)
        # bangs: swept locks with a parting
        def front(dd):
            poly([(112, 270), (118, 196), (196, 124), (330, 114), (436, 186), (448, 270), (430, 250), (300, 240), (170, 255)], navy, dd)
            for root, ctrl, tip, wd in (((178, 134), (140, 240), (180, 346), 84), ((262, 126), (220, 210), (222, 300), 84),
                                        ((330, 126), (372, 200), (338, 292), 84), ((404, 140), (434, 220), (404, 300), 60)):
                poly(lock_pts(root, ctrl, tip, wd), navy, dd)
        put(layer(front, navy, 2))
        # pigtails with small red ties
        def tails(dd):
            ell((80, 470, 206, 650), navy, dd); ell((354, 470, 480, 650), navy, dd)
            poly(lock_pts((160, 440), (150, 470), (136, 520), 54), navy, dd); poly(lock_pts((400, 440), (410, 470), (424, 520), 54), navy, dd)
        put(layer(tails, navy, 6))
        ell((146, 456, 170, 486), (206, 54, 64)); ell((390, 456, 414, 486), (206, 54, 64))
        for root, ctrl, tip in (((170, 140), (130, 220), (168, 320)), ((260, 130), (222, 180), (232, 250)), ((406, 150), (432, 220), (404, 290))):
            line(_bez(root, ctrl, tip, 10), navy_l, 6)
        line(_bez((110, 520), (100, 570), (130, 620), 10), navy_l, 5); line(_bez((450, 520), (460, 570), (430, 620), 10), navy_l, 5)
        d.arc(P(178, 298, 244, 326), 200, 340, fill=navy_d, width=int(5 * S)); d.arc(P(316, 298, 382, 326), 200, 340, fill=navy_d, width=int(5 * S))
        _eyes(d, P, S, blink, lash=True)
    ell((166, 398, 210, 422), (252, 190, 190)); ell((350, 398, 394, 422), (252, 190, 190))   # small blush
    _mouth(d, P, S, mouth)
    return im.resize((int(560 * CHAR_SCALE), int(760 * CHAR_SCALE)), Image.LANCZOS)



def _new_character(name, mouth, blink):
    """Four independently drawn character rigs in the established soft chibi style."""
    S = 2 * CHAR_SCALE
    im = Image.new("RGBA", (int(560*S), int(760*S)), (0,0,0,0))
    d = ImageDraw.Draw(im)
    def P(v): return tuple(int(a*S) for a in v)
    def E(b,c,o=None,w=1): d.ellipse(P(b),fill=c,outline=o,width=max(1,int(w*S)))
    def G(pts,c,o=None,w=1):
        q=[P(p) for p in pts]; d.polygon(q,fill=c)
        if o: d.line(q+[q[0]],fill=o,width=max(1,int(w*S)),joint="curve")
    def L(pts,c,w=4): d.line([P(p) for p in pts],fill=c,width=max(1,int(w*S)),joint="curve")
    skin=(253,227,203); ink=(92,52,56); blush=(252,177,177); white=(255,250,241)
    if name=="Camille":
        hair=(151,70,49); dark=(105,43,39); outfit=(221,174,72); iris=(92,126,91)
        # short rounded curly bob, cheek-framing ringlets
        E((104,105,456,500),dark)
        for x,y,r in [(145,190,58),(205,130,62),(280,112,65),(355,132,62),(420,205,58),(118,330,48),(442,330,48),(155,410,42),(405,410,42)]: E((x-r,y-r,x+r,y+r),hair)
        G([(95,760),(112,585),(175,505),(225,480),(335,480),(385,505),(448,585),(465,760)],outfit)
        G([(225,482),(280,555),(335,482),(320,760),(240,760)],(255,221,153))
        E((145,160,415,475),skin)
        G([(130,270),(140,165),(205,115),(235,225),(190,270)],hair)
        G([(235,220),(280,115),(345,130),(330,245)],hair)
        for x,y in [(148,275),(412,275),(155,365),(405,365)]: E((x-25,y-28,x+25,y+28),hair)
        for x,y in [(235,390),(255,400),(275,393),(295,400),(315,390)]: E((x-3,y-3,x+3,y+3),(176,105,83))
        # round spectacles
        for x in (214,346): d.ellipse(P((x-39,318,x+39,396)),outline=(105,66,52),width=int(6*S))
        L([(253,356),(307,356)],(105,66,52),5)
    elif name=="Théo":
        hair=(76,52,39); dark=(43,34,32); outfit=(54,155,147); iris=(67,139,91)
        # tall spiky/quiff silhouette, broad jaw
        E((120,110,440,455),dark)
        G([(120,265),(132,165),(190,120),(205,62),(250,130),(296,55),(326,130),(390,92),(440,190),(425,285),(350,235),(285,280),(215,235),(160,290)],hair)
        G([(100,760),(125,570),(190,500),(230,475),(330,475),(370,500),(435,570),(460,760)],outfit)
        G([(205,495),(280,600),(355,495),(328,760),(232,760)],(37,116,112))
        L([(250,545),(240,650)],white,5); L([(310,545),(320,650)],white,5)
        E((142,155,418,470),skin)
        G([(148,315),(170,420),(228,478),(280,492),(332,478),(390,420),(412,315)],skin)
        G([(130,255),(145,155),(220,112),(335,110),(430,190),(420,265),(352,220),(286,270),(224,230),(170,285)],hair)
        # over-ear headphones
        d.arc(P((100,145,460,475)),190,350,fill=(35,38,43),width=int(13*S))
        E((80,290,145,390),(43,48,54)); E((415,290,480,390),(43,48,54))
        E((96,304,132,378),(100,111,118)); E((428,304,464,378),(100,111,118))
    elif name=="Chloé":
        hair=(166,116,72); dark=(112,75,49); outfit=(177,157,220); iris=(86,110,142)
        # long curtain hair with straight tapered lengths
        E((100,95,460,660),dark)
        G([(112,205),(145,115),(250,88),(368,110),(445,210),(445,640),(390,700),(375,330),(180,330),(165,700),(110,640)],hair)
        G([(112,760),(128,575),(190,510),(232,485),(328,485),(370,510),(432,575),(448,760)],outfit)
        G([(230,485),(280,555),(330,485),(315,760),(245,760)],(220,207,244))
        G([(250,500),(280,555),(310,500),(280,590)],(255,239,250))
        E((142,155,418,470),skin)
        G([(150,330),(165,430),(220,480),(280,492),(340,480),(395,430),(410,330)],skin)
        G([(112,255),(140,155),(250,105),(370,130),(445,230),(410,285),(350,218),(290,252),(220,220),(160,285)],hair)
        L([(145,194),(210,130),(330,128),(410,196)],(236,202,164),12)
        E((374,178,414,218),(238,177,197)); E((388,166,400,230),(255,226,235))
    elif name == "Félix":
        hair=(247,190,82); hair_light=(255,218,135); hair_shadow=(220,151,55)
        dark=(35,31,39); outfit=(37,31,39); iris=(112,132,82)
        # Full golden hair silhouette behind the head, with two clearly separate cat ears.
        G([(105,230),(88,120),(178,145),(205,62),(270,130),(355,58),(390,145),(475,112),(450,255),(430,390),(380,440),(170,440),(120,380)],hair_shadow)
        G([(120,220),(105,118),(184,145),(207,75),(270,145),(350,70),(382,150),(455,125),(438,250)],dark)
        G([(150,190),(130,128),(185,154),(207,96),(270,158),(350,92),(380,160),(432,145),(420,230)],hair)
        # Soft inner ear panels make the cat ears read as ears, not stray hair behind him.
        G([(151,145),(139,133),(183,154),(204,111),(225,160)],hair_shadow)
        G([(326,160),(350,108),(377,163),(419,148),(400,180)],hair_shadow)
        # Face and jaw sit in front of the rear hair mass.
        E((142,155,418,470),skin)
        G([(150,315),(160,408),(215,465),(280,480),(345,465),(400,408),(410,315)],skin)
        # Thick golden fringe, rounded side locks, and layered tufts frame the face.
        G([(116,278),(126,190),(170,133),(228,112),(286,118),(345,105),(411,154),(444,225),(425,280),(397,250),(374,292),(342,258),(310,294),(278,255),(244,291),(214,254),(181,290),(155,252)],hair)
        G([(125,245),(146,185),(187,146),(220,137),(199,212),(172,264)],hair_light)
        G([(230,190),(263,125),(300,128),(285,221),(258,254)],hair_shadow)
        G([(315,185),(350,137),(390,164),(410,222),(378,265),(358,229)],hair_light)
        # Side locks stay attached to the head and fall beside the cheeks.
        G([(130,240),(112,315),(135,380),(165,405),(157,330),(176,270)],hair)
        G([(430,238),(448,315),(425,380),(395,405),(403,330),(384,270)],hair)
        # Black cat suit and gold bell collar.
        G([(112,760),(140,540),(190,480),(370,480),(420,540),(448,760)],outfit)
        G([(245,478),(280,540),(315,478)],(66,58,65))
        E((255,470,305,525),(247,208,120)); E((270,490,290,510),(92,52,56))
        # Eye mask sits over the face, below the fringe.
        G([(145,325),(170,290),(220,300),(280,325),(340,300),(390,290),(415,325),(390,385),(345,390),(280,370),(215,390),(170,385)],dark)
        # Fine highlights add volume without making the hair look detached.
        L([(176,174),(210,148),(244,142)],hair_light,5)
        L([(324,145),(357,151),(385,178)],hair_light,5)
    elif name == "Zoé":
        hair=(48,61,112); dark=(38,34,46); outfit=(218,54,58); iris=(105,75,78)
        # blue twin pigtails tied with bright red ribbons
        E((65,300,205,620),hair); E((355,300,495,620),hair)
        G([(110,760),(135,535),(190,485),(370,485),(425,535),(450,760)],outfit)
        E((100,100,460,500),dark)
        E((142,155,418,470),skin)
        G([(110,265),(125,180),(205,115),(325,110),(430,180),(450,270),(410,245),(360,285),(300,235),(240,280),(180,245)],hair)
        # red mask and polka-dot top
        G([(145,325),(170,292),(220,300),(280,325),(340,300),(390,292),(415,325),(390,385),(345,390),(280,370),(215,390),(170,385)],(224,45,52))
        for x,y in [(225,560),(335,560),(260,650),(360,700),(195,700)]: E((x-13,y-13,x+13,y+13),(38,38,48))
        E((125,190,165,230),(225,45,52)); E((395,190,435,230),(225,45,52))
    else: # Lucas
        hair=(37,34,39); dark=(22,20,25); outfit=(174,91,61); iris=(62,96,120)
        # tousled wavy dark hair, squarer jaw, layered casual jacket
        E((100,100,460,500),dark)
        G([(112,260),(130,165),(205,112),(330,112),(430,185),(435,260),(390,232),(355,278),(300,235),(250,280),(190,235),(150,285)],hair)
        for y in (152,184,216): d.arc(P((160,y,410,y+90)),190,345,fill=(100,91,96),width=int(7*S))
        G([(72,760),(100,580),(170,505),(225,480),(335,480),(390,505),(460,580),(488,760)],outfit)
        G([(220,480),(280,570),(340,480),(365,760),(195,760)],(245,223,197))
        G([(245,492),(315,492),(340,670),(280,710),(220,670)],(58,91,103))
        L([(246,520),(280,680),(318,520)],(87,128,138),8)
        E((142,155,418,470),skin)
        G([(142,315),(158,415),(205,470),(240,488),(320,488),(355,470),(402,415),(418,315)],skin)
        G([(115,260),(130,165),(205,112),(330,112),(430,185),(435,260),(390,232),(355,278),(300,235),(250,280),(190,235),(150,285)],hair)
        L([(185,292),(225,280)],dark,7)
        E((407,385,427,405),(221,177,116))
    # Face details. Félix and Zoé get individually shaped eyes instead of the default cast eyes.
    E((120,305,166,390),skin); E((394,305,440,390),skin)
    if name == "Félix":
        # Bright, balanced cat-like green eyes: almond silhouette, clear iris and two soft catchlights.
        for ex in (214,346):
            side = -1 if ex < 280 else 1
            if blink:
                d.arc(P((ex-28,350,ex+28,389)),195,345,fill=(35,29,34),width=int(7*S))
                d.line(P((ex+side*27,365,ex+side*39,354)),fill=(35,29,34),width=int(5*S))
            else:
                G([(ex-29,358),(ex-22,333),(ex,325),(ex+22,333),(ex+29,358),(ex+17,389),(ex,397),(ex-17,389)],(42,31,37))
                G([(ex-23,357),(ex-17,338),(ex,332),(ex+17,338),(ex+23,357),(ex+14,384),(ex,390),(ex-14,384)],(255,250,241))
                E((ex-15,344,ex+15,389),(119,151,83))
                E((ex-8,346,ex+9,384),(39,35,32))
                E((ex-10,337,ex+2,351),(255,255,255))
                E((ex+7,366,ex+13,374),(255,255,255))
                d.arc(P((ex-29,326,ex+29,365)),195,345,fill=(35,29,34),width=int(7*S))
                d.line(P((ex+side*25,345,ex+side*38,333)),fill=(35,29,34),width=int(5*S))
    elif name == "Zoé":
        # Warm chocolate-brown, rounder expressive eyes with a soft red-mask edge and lashes.
        for ex in (214,346):
            side = -1 if ex < 280 else 1
            if blink:
                d.arc(P((ex-29,350,ex+29,390)),195,345,fill=(52,30,37),width=int(7*S))
                d.line(P((ex+side*27,365,ex+side*39,353)),fill=(52,30,37),width=int(5*S))
            else:
                E((ex-29,325,ex+29,399),(48,30,38))
                E((ex-24,331,ex+24,393),(255,250,241))
                E((ex-18,342,ex+18,392),(133,77,70))
                E((ex-10,344,ex+11,387),(48,31,35))
                E((ex-13,334,ex+2,351),(255,255,255))
                E((ex+8,369,ex+15,379),(255,255,255))
                d.arc(P((ex-31,321,ex+31,365)),195,345,fill=(52,30,37),width=int(8*S))
                d.line(P((ex+side*26,345,ex+side*42,331)),fill=(52,30,37),width=int(6*S))
    else:
        for ex in (214,346):
            d.arc(P((ex-31,300,ex+31,340)),195,345,fill=dark,width=int(7*S))
            if blink:
                d.arc(P((ex-28,345,ex+28,390)),200,340,fill=ink,width=int(7*S))
            else:
                E((ex-25,326,ex+25,397),(58,35,43))
                E((ex-17,348,ex+17,392),iris)
                E((ex-12,332,ex+5,352),(255,255,255))
                E((ex+5,368,ex+15,380),(255,255,255))
    E((166,398,210,422),blush); E((350,398,394,422),blush)
    if mouth==0: d.arc(P((262,410,298,436)),15,165,fill=ink,width=int(5*S))
    elif mouth==1: E((268,414,292,438),(128,48,62))
    else: E((260,410,300,446),(128,48,62)); E((268,430,292,444),(238,128,140))
    return im.resize((int(560*CHAR_SCALE),int(760*CHAR_SCALE)),Image.LANCZOS)


@functools.lru_cache(maxsize=128)
def sprite(name, mouth, blink):
    """Render the eight cast designs; Adrien and Marinette remain unchanged."""
    if name in ("Adrien", "Marinette"):
        return _sprite_base(name, mouth, blink)
    if name in ("Camille", "Théo", "Chloé", "Lucas", "Félix", "Zoé"):
        return _new_character(name, mouth, blink)
    raise ValueError(f"Unknown character: {name}")
