"""Story mode from plain dialogue.

The same script you write for Small mode (title:, optional scene:, `Adrien: Bonjour ! | Hello!` lines, `vocab:` lines)
is turned into a fully directed story: the place is chosen from what the characters talk about, they enter and walk
to the named spots of that place (counter, table, bench...), move again as the conversation goes on, wave, react, and
pick up / eat / drink the food they ask for. A script with a [story] section is parsed as before (hand-directed).
"""
import re
from . import scenes as SC
from .config import CHARS, W
from .acting import MIN_GAP
from .parser import Script, Say, Direction, SceneChange, Vocab, SECTION, ScriptError, parse_script

GREET = re.compile(r"\b(bonjour|salut|coucou|bonsoir|hello)\b", re.I)
BYE = re.compile(r"(au revoir|à demain|à bientôt|a bientôt|à plus|bonne journée|bonne soirée)", re.I)
THANKS = re.compile(r"\b(merci|bravo|super|génial|parfait|excellent|délicieux|magnifique)\b", re.I)
REQUEST = re.compile(r"(je voudrais|je veux|je prends|j'aimerais|s'il (vous|te) plaît)", re.I)
ITEMS = [("croissant", "croissant", "eats"), ("baguette", "baguette", "eats"), ("macaron", "macaron", "eats"),
         ("glace", "ice cream", "eats"), ("café", "coffee", "drinks"), ("jus", "juice", "drinks")]
ITEM_SCENES = ("bakery", "cafe", "restaurant")
ENTRANCE = ("entrance", "door")
MOVE_EVERY = 3                      # a character changes spot every 3rd line of the conversation


def parse_plain(text):
    meta, says, vocab = {}, [], []
    for i, raw in enumerate(text.replace("\ufeff", "").splitlines(), 1):
        s = raw.strip()
        if not s or s.startswith("#"): continue
        m = re.match(r"^(title|scene|episode|cover|cast)\s*:\s*(.+)$", s, re.I)
        if m: meta[m[1].lower()] = m[2].strip(); continue
        m = re.match(r"^vocab\s*:\s*(.+)$", s, re.I)
        if m:
            p = [x.strip() for x in m[1].split("|")]
            if len(p) not in (2, 3) or not all(p):
                raise ScriptError(f"line {i}: vocab needs 'French | English' (or 'French | pronunciation | English').")
            vocab.append((p[0], p[-1])); continue
        m = re.match(r"^([A-Za-zÀ-ÿ]+)\s*[:：]\s*(.+)$", s)
        if m and m[1].capitalize() in CHARS:
            p = [x.strip() for x in m[2].split("|")]
            if len(p) < 2 or not p[0] or not p[1]:
                raise ScriptError(f"line {i}: add the English after a | sign, like 'Adrien: Bonjour ! | Hello!'.")
            says.append(Say(m[1].capitalize(), p[0], p[1], p[2] if len(p) > 2 else "", i)); continue
        raise ScriptError(f"line {i}: can't read this line (speakers are {' and '.join(CHARS)}): {s[:60]}")
    if not meta.get("title"): raise ScriptError("missing 'title:' in the header")
    if not says: raise ScriptError("no spoken lines (write lines like 'Adrien: Bonjour ! | Hello!')")
    return meta, says, vocab[:5]


def _spots(scene):
    sp = SC.SCENES[scene]["spots"]
    standing = sorted(((n, x) for n, x in sp.items() if n not in ENTRANCE), key=lambda kv: kv[1])
    if len(standing) < 2: standing = sorted(sp.items(), key=lambda kv: kv[1])
    near = lambda target: min(standing, key=lambda kv: abs(kv[1] - target))
    a, b = near(W * 0.3), near(W * 0.7)
    if a[0] == b[0] or abs(a[1] - b[1]) < MIN_GAP:
        a = standing[0]; b = max(standing, key=lambda kv: abs(kv[1] - a[1]))
    return a, b, standing


def direct(meta, says, vocab, items=True):
    probe = Script(dict(meta), list(says), [], [], [])
    scene = SC.scene_for(probe)
    if not scene:
        raise ScriptError(f"unknown scene {meta.get('scene')!r}; use one of: auto, {', '.join(SC.SCENES)}")
    meta = dict(meta, scene=scene)
    a, b, standing = _spots(scene)
    declared_cast = [n.strip() for n in meta.get("cast", "").split(",") if n.strip()]
    names = declared_cast or list(dict.fromkeys(s.speaker for s in says))
    if not declared_cast and len(names) == 1:
        names.append(next((n for n in CHARS if n != names[0]), "Adrien"))
    if len(names) != 2 or any(n not in CHARS for n in names):
        raise ScriptError(f"Story mode cast must contain exactly two known characters; found: {', '.join(names)}")
    if any(s.speaker not in names for s in says):
        raise ScriptError("Every dialogue speaker must be one of the two characters in cast:.")
    at = {names[0]: a, names[1]: b}                   # current spot (name, x) of each character
    first = says[0].line
    ev = [SceneChange(scene, first),
          Direction(f"{names[0]} enters left to {a[0]}", False, first),
          Direction(f"{names[1]} enters right to {b[0]}", True, first)]
    orders, rot = [], 0                                 # food/drink requests: asked at line i, bought after the reply, enjoyed after that
    for i, s in enumerate(says):
        me, other = s.speaker, [n for n in names if n != s.speaker][0]
        D = lambda text, sim=False: Direction(text, sim, s.line)
        if i == 0 and GREET.search(s.fr):
            ev.append(D(f"{me} waves"))
        elif i > 0 and i % MOVE_EVERY == 0 and len(standing) > 2:
            far = [(n, x) for n, x in standing if n != at[me][0] and abs(x - at[other][1]) >= MIN_GAP + 20]
            if far:
                at[me] = far[rot % len(far)]; rot += 1
                ev.append(D(f"{me} walks to {at[me][0]}"))
        ev.append(s)
        for o in list(orders):                           # the reply came: the customer buys; one line later they enjoy it
            if o["stage"] == 0 and i == o["i"] + 1:
                ev.append(D(f"{o['who']} buys a {o['item']}")); o["stage"] = 1
            elif o["stage"] == 1 and i >= o["i"] + 2:
                ev.append(D(f"{o['who']} {o['verb']} the {o['item']}"))
                if o["verb"] == "drinks": ev.append(D(f"{o['who']} puts away the {o['item']}", True))
                orders.remove(o)
        if items and scene in ITEM_SCENES and REQUEST.search(s.fr) and not any(o["who"] == me for o in orders):
            low = s.fr.lower()
            for key, item, verb in ITEMS:
                if re.search(r"\b" + key, low):
                    orders.append(dict(who=me, item=item, verb=verb, i=i, stage=0)); break
        if i == len(says) - 1 and BYE.search(s.fr):
            ev.append(D("Both wave"))
        elif THANKS.search(s.fr):
            ev.append(D(f"{other} looks happy"))
        elif s.fr.rstrip().endswith("!") and i < len(says) - 1 and not orders:
            ev.append(D(f"{other} nods"))
    voc = []
    for fr, en in vocab:
        key = re.sub(r"[^\w' ]", "", fr.lower()).strip()
        ex = next(((s.fr, s.en) for s in says if key and key in re.sub(r"[^\w' ]", "", s.fr.lower())), None)
        voc.append(Vocab(fr, en, [ex] if ex else []))
    return Script(meta, ev, voc, [], [])


def parse_any(text):
    """Hand-directed script ([story] ...) as before, or plain dialogue that gets directed automatically."""
    from .acting import check
    if any(SECTION.match(l.strip()) for l in text.replace("\ufeff", "").splitlines()):
        return parse_script(text)
    meta, says, vocab = parse_plain(text)
    script = direct(meta, says, vocab)
    try:
        check(script)
    except ScriptError:                                 # a prop rule was not met: tell the story without props
        script = direct(meta, says, vocab, items=False); check(script)
    return script
