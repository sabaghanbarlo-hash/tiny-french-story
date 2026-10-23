"""Stage directions -> timeline. The vocabulary here IS the supported list (see DIRECTING.md); anything else is a ScriptError."""
import bisect, math, re
from dataclasses import dataclass
from .config import W
from .parser import ScriptError, Say, Direction, SceneChange
from . import scenes as SC
from . import items as IT

NAMES = ("Camille", "Julien")
HOME = {"Camille": 300, "Julien": 780}
SPEED, RUN = 500.0, 820.0
MIN_GAP = 190
EXPRS = {"neutral": "neutral", "happy": "happy", "glad": "happy", "smiling": "happy", "sad": "sad", "confused": "confused", "puzzled": "confused",
         "surprised": "surprised", "shocked": "surprised", "embarrassed": "embarrassed", "worried": "worried", "nervous": "worried", "excited": "excited",
         "thrilled": "excited", "shy": "shy"}
GESTURES = {"waves": ("wave", 1.5), "jumps": ("jump", 0.9), "laughs": ("laugh", 1.5), "nods": ("nod", 1.0), "cheers": ("cheer", 1.6)}
VERB_LIST = ["enters left|right [to <spot>]", "exits left|right", "walks to <spot>", "runs to <spot>", "looks <feeling>", "looks at <name>", "faces <name|left|right>",
             "waves", "jumps", "laughs", "nods", "cheers", "holds <item>", "picks up <item>", "buys <item>", "eats [item]", "drinks [item]",
             "drops|puts away|finishes [item]", "gives <item> to <name>", "wait <seconds>"]
BASE_VERBS = {"enter": "enters", "exit": "exits", "walk": "walks", "run": "runs", "go": "goes", "move": "moves", "look": "looks", "face": "faces", "wave": "waves",
              "jump": "jumps", "laugh": "laughs", "nod": "nods", "cheer": "cheers", "hold": "holds", "take": "takes", "pick": "picks", "buy": "buys", "eat": "eats",
              "drink": "drinks", "drop": "drops", "put": "puts", "finish": "finishes", "give": "gives"}
_ART = re.compile(r"^(?:the|a|an|his|her)\s+")

@dataclass
class Op:
    who: str; verb: str; arg: str; ln: int

def _who(tok):
    return list(NAMES) if tok == "both" else [tok.title()]

def parse_dir(text, ln=0):
    t = re.sub(r"\s+", " ", text.strip().rstrip(".!").lower())
    m = re.match(r"^wait (?:for )?(\d+(?:\.\d+)?)(?: seconds?| s)?$", t)
    if m: return [Op("", "wait", m.group(1), ln)]
    m = re.match(r"^(camille|julien|both)\s+(.+)$", t)
    if not m: raise ScriptError(f"line {ln}: a direction must start with Camille, Julien or both (or be 'wait N'): {text!r}")
    ops, rest = [], m.group(2)
    first, _, tail = rest.partition(" ")
    rest = BASE_VERBS.get(first, first) + (" " + tail if tail else "")
    def add(verb, arg=""):
        for w in _who(m.group(1)): ops.append(Op(w, verb, arg, ln))
    for pat, verb in ((r"^enters (left|right)(?: to (.+))?$", "enter"), (r"^exits (left|right)$", "exit")):
        mm = re.match(pat, rest)
        if mm: add(verb, " to ".join(x for x in mm.groups() if x)); return ops
    mm = re.match(r"^(walks|runs|goes|moves) to (.+)$", rest)
    if mm: add("run" if mm.group(1) == "runs" else "walk", _ART.sub("", mm.group(2))); return ops
    mm = re.match(r"^looks at (.+)$", rest)
    if mm: add("lookat", _ART.sub("", mm.group(1))); return ops
    mm = re.match(r"^looks (\w+)$", rest)
    if mm:
        if mm.group(1) not in EXPRS: raise ScriptError(f"line {ln}: unsupported feeling {mm.group(1)!r}; supported: {', '.join(sorted(set(EXPRS)))}")
        add("expr", EXPRS[mm.group(1)]); return ops
    mm = re.match(r"^faces (.+)$", rest)
    if mm: add("face", _ART.sub("", mm.group(1))); return ops
    if rest in GESTURES: add("gesture", rest); return ops
    mm = re.match(r"^(holds|takes|picks up|picks|buys) (.+)$", rest)
    if mm:
        verb = mm.group(1); obj = mm.group(2)
        if verb == "picks": 
            if not obj.startswith("up "): raise ScriptError(f"line {ln}: unsupported direction {text!r}. Supported: " + "; ".join(VERB_LIST))
            obj = obj[3:]; verb = "picks up"
        it = IT.find(obj)
        if not it: raise ScriptError(f"line {ln}: unsupported item {obj!r}; supported items: {', '.join(IT.ITEMS)}")
        add({"holds": "hold", "takes": "pickup", "picks up": "pickup", "buys": "buy"}[verb], it); return ops
    mm = re.match(r"^(eats|drinks)(?: (.+))?$", rest)
    if mm:
        it = IT.find(mm.group(2)) if mm.group(2) else ""
        if mm.group(2) and not it: raise ScriptError(f"line {ln}: unsupported item {mm.group(2)!r}; supported items: {', '.join(IT.ITEMS)}")
        add("eat" if mm.group(1) == "eats" else "drink", it or ""); return ops
    mm = re.match(r"^(?:drops|finishes|puts away|puts)(?: (.+?))?(?: away)?$", rest)
    if mm: add("drop", (IT.find(mm.group(1)) or "") if mm.group(1) else ""); return ops
    mm = re.match(r"^gives (.+?) to (camille|julien)$", rest)
    if mm:
        what = mm.group(1); it = "" if what in ("it", "that", "them") else IT.find(what)
        if what not in ("it", "that", "them") and not it: raise ScriptError(f"line {ln}: unsupported item {what!r}; supported items: {', '.join(IT.ITEMS)}")
        add("give", f"{it}|{mm.group(2).title()}"); return ops
    raise ScriptError(f"line {ln}: unsupported direction {text!r}. Supported: " + "; ".join(VERB_LIST))

def _ss(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)

class Stage:
    def __init__(self, scene, starts_off=()):
        self.scene = scene
        self.pos = {n: [] for n in NAMES}; self.expr = {n: [(-1, "neutral")] for n in NAMES}; self.item = {n: [(-1, None, 0)] for n in NAMES}
        self.face = {n: [(-1, "auto")] for n in NAMES}; self.acts = {n: [] for n in NAMES}
        self.cur = {}
        for n in NAMES:
            x = -300 if n in starts_off else HOME[n]
            self.cur[n] = dict(x=x, on=n not in starts_off, item=None, bites=0)
            self.pos[n].append((-1, -0.5, x, x, 0))

    def other(self, n): return NAMES[1] if n == NAMES[0] else NAMES[0]
    def spots(self): return SC.SCENES[self.scene]["spots"]
    def cut(self, t, scene, starts_off=()):
        self.scene = scene
        for n in NAMES:
            x = -300 if n in starts_off else HOME[n]
            self.cur[n]["x"] = x; self.cur[n]["on"] = n not in starts_off; self.pos[n].append((t, t, x, x, 0)); self.face[n].append((t, "auto"))
    def resolve(self, n, arg, ln):
        a = arg.strip()
        if a in ("left", "right", "center", "centre", "home"):
            return {"left": 150, "right": W - 150, "center": W // 2, "centre": W // 2, "home": HOME[n]}[a]
        m = re.match(r"^(\d{1,3})\s*%$", a)
        if m: return W * int(m.group(1)) / 100
        m = re.match(r"^next to (camille|julien)$", a)
        if m:
            tgt = self.cur[m.group(1).title()]
            if not tgt["on"]: raise ScriptError(f"line {ln}: {m.group(1).title()} is not on stage to stand next to")
            side = 1 if self.cur[n]["x"] >= tgt["x"] else -1
            return min(W - 130, max(130, tgt["x"] + side * 200))
        sp = self.spots()
        if a in sp: return sp[a]
        raise ScriptError(f"line {ln}: unknown place {arg!r} in the {self.scene}. Spots here: {', '.join(sp)}; or left, center, right, home, next to <name>, 40%")
    def sep(self, n, x, came_from):
        o = self.other(n); oc = self.cur[o]
        if not oc["on"] or abs(x - oc["x"]) >= MIN_GAP: return x
        side = 1 if came_from >= oc["x"] else -1
        nx = oc["x"] + side * MIN_GAP
        if nx < 130 or nx > W - 130: nx = oc["x"] - side * MIN_GAP
        return min(W - 130, max(130, nx))
    def _move(self, n, s, x1, run, ln):
        c = self.cur[n]; x0 = c["x"]; dur = max(abs(x1 - x0) / (RUN if run else SPEED), 0.01)
        self.pos[n].append((s, s + dur, x0, x1, 1 if run else 0)); c["x"] = x1
        if x1 != x0: self.face[n].append((s, 1 if x1 > x0 else -1)); self.face[n].append((s + dur, "auto"))
        return s + dur
    def _act(self, n, s, name, dur): self.acts[n].append((s, s + dur, name)); return s + dur
    def _setitem(self, n, t, item, bites=0):
        self.item[n].append((t, item, bites)); self.cur[n]["item"] = item; self.cur[n]["bites"] = bites
    def _need_on(self, n, ln):
        if not self.cur[n]["on"]: raise ScriptError(f"line {ln}: {n} is not on stage (use 'enters left/right' first)")

    def run_beat(self, t, ops):
        cursor = {n: t for n in NAMES}; end = t; enter_delay = {}
        for op in ops:
            if op.verb == "wait":
                end = max(end, t + float(op.arg)); continue
            n, ln = op.who, op.ln; c = self.cur[n]; s = cursor[n]
            if op.verb == "enter":
                side, _, spot = op.arg.partition(" to ")
                if c["on"]: raise ScriptError(f"line {ln}: {n} is already on stage; use 'walks to' instead of 'enters'")
                x0 = -240 if side == "left" else W + 240
                k = enter_delay.get(side, 0); enter_delay[side] = k + 1; s += 0.4 * k
                tgt = self.sep(n, self.resolve(n, spot, ln) if spot else HOME[n], x0)
                c["x"] = x0; c["on"] = True; self.pos[n].append((s, s, x0, x0, 0))
                cursor[n] = self._move(n, s, tgt, False, ln)
            elif op.verb in ("walk", "run"):
                self._need_on(n, ln); tgt = self.sep(n, self.resolve(n, op.arg, ln), c["x"])
                cursor[n] = self._move(n, s, tgt, op.verb == "run", ln)
            elif op.verb == "exit":
                self._need_on(n, ln); cursor[n] = self._move(n, s, -260 if op.arg == "left" else W + 260, False, ln); c["on"] = False
            elif op.verb == "expr":
                self._need_on(n, ln); self.expr[n].append((s, op.arg)); cursor[n] = s + 0.35
            elif op.verb == "lookat":
                self._need_on(n, ln); a = op.arg
                if a in ("camille", "julien"):
                    tg = a.title(); self._need_on(tg, ln); self.face[n].append((s, 1 if self.cur[tg]["x"] >= c["x"] else -1))
                else:
                    x = self.resolve(n, a, ln); self.face[n].append((s, 1 if x >= c["x"] else -1))
                cursor[n] = s + 0.4
            elif op.verb == "face":
                self._need_on(n, ln); a = op.arg
                if a in ("left", "right"): self.face[n].append((s, -1 if a == "left" else 1))
                elif a in ("camille", "julien"): self._need_on(a.title(), ln); self.face[n].append((s, 1 if self.cur[a.title()]["x"] >= c["x"] else -1))
                else: raise ScriptError(f"line {ln}: 'faces' needs Camille, Julien, left or right (got {a!r})")
                cursor[n] = s + 0.3
            elif op.verb == "gesture":
                self._need_on(n, ln); name, dur = GESTURES[op.arg]; cursor[n] = self._act(n, s, name, dur)
            elif op.verb in ("hold", "pickup", "buy"):
                self._need_on(n, ln)
                if c["item"] and c["item"] != op.arg: raise ScriptError(f"line {ln}: {n} is already holding {c['item']}; drop or give it first")
                if op.verb == "hold": self._setitem(n, s, op.arg); cursor[n] = s + 0.4
                elif op.verb == "pickup": self._act(n, s, "bend", 0.9); self._setitem(n, s + 0.45, op.arg); cursor[n] = s + 0.9
                else: self._act(n, s, "hop", 0.9); self._setitem(n, s + 0.4, op.arg); cursor[n] = s + 0.9
            elif op.verb in ("eat", "drink"):
                self._need_on(n, ln); it = op.arg or c["item"]
                if not it: raise ScriptError(f"line {ln}: {n} has nothing to {op.verb}; give them an item first")
                if c["item"] and c["item"] != it: raise ScriptError(f"line {ln}: {n} is holding {c['item']}, not {it}")
                if op.verb == "eat" and it not in IT.EDIBLE: raise ScriptError(f"line {ln}: {it} cannot be eaten (edible: {', '.join(sorted(IT.EDIBLE))})")
                if op.verb == "drink" and it not in IT.DRINKABLE: raise ScriptError(f"line {ln}: {it} cannot be drunk (drinkable: {', '.join(sorted(IT.DRINKABLE))})")
                if not c["item"]: self._setitem(n, s, it)
                if op.verb == "eat":
                    self._act(n, s, "eat", 2.7)
                    for k in (1, 2): self._setitem(n, s + 0.9 * k, it, k)
                    self._setitem(n, s + 2.7, None); cursor[n] = s + 2.8
                else: self._act(n, s, "drink", 1.9); cursor[n] = s + 2.0
            elif op.verb == "drop":
                self._need_on(n, ln)
                if not c["item"]: raise ScriptError(f"line {ln}: {n} is not holding anything to put away")
                if op.arg and op.arg != c["item"]: raise ScriptError(f"line {ln}: {n} is holding {c['item']}, not {op.arg}")
                self._act(n, s, "bend", 0.7); self._setitem(n, s + 0.35, None); cursor[n] = s + 0.7
            elif op.verb == "give":
                self._need_on(n, ln); it, _, tg = op.arg.partition("|"); r = self.cur[tg]
                if tg == n: raise ScriptError(f"line {ln}: {n} cannot give something to themselves")
                self._need_on(tg, ln)
                if not c["item"]: raise ScriptError(f"line {ln}: {n} is not holding anything to give")
                if it and it != c["item"]: raise ScriptError(f"line {ln}: {n} is holding {c['item']}, not {it}")
                if r["item"]: raise ScriptError(f"line {ln}: {tg} is already holding {r['item']}; they need to put it away first")
                if abs(r["x"] - c["x"]) > 250:
                    side = 1 if c["x"] >= r["x"] else -1; s = self._move(n, s, min(W - 130, max(130, r["x"] + side * 210)), False, ln)
                self.face[n].append((s, 1 if r["x"] >= c["x"] else -1))
                thing = c["item"]; self._act(n, s, "give", 1.4); self._setitem(n, s + 0.7, None); self._setitem(tg, s + 0.7, thing)
                cursor[n] = s + 1.4; cursor[tg] = max(cursor[tg], s + 1.4)
            end = max(end, cursor[n])
        return end

    def basic(self, n, t):
        ps = self.pos[n]; i = bisect.bisect_right([p[0] for p in ps], t) - 1; p = ps[max(i, 0)]
        t0, t1, x0, x1, run = p
        moving = t0 <= t < t1 and x0 != x1
        x = x0 + (x1 - x0) * _ss((t - t0) / (t1 - t0)) if moving else (x1 if t >= t1 else x0)
        return x, moving
    def _last(self, lst, t):
        i = bisect.bisect_right([e[0] for e in lst], t) - 1
        return lst[max(i, 0)]
    def pose(self, n, t):
        x, moving = self.basic(n, t); o = self.other(n); ox, omoving = self.basic(o, t)
        vis = -230 < x < W + 230; ovis = -230 < ox < W + 230
        fv = self._last(self.face[n], t)[1]
        if fv == "auto":
            fv = (1 if ox >= x else -1) if ovis and vis and abs(ox - x) > 1 else (1 if n == "Camille" else -1)
        expr = self._last(self.expr[n], t)[1]; it = self._last(self.item[n], t)
        act, ap = None, 0.0
        for a0, a1, nm in self.acts[n]:
            if a0 <= t < a1: act, ap = nm, (t - a0) / (a1 - a0)
        lane = 0.0
        if moving and ovis and not (omoving and n == "Camille"):
            lane = -70 * _ss(1 - (abs(x - ox) - 90) / 150)
        return dict(x=x, vis=vis, moving=moving, face=fv, expr=expr, act=act, ap=ap, item=it[1], bites=it[2], lane=lane, walking=1.0 if moving else 0.0, phase=x / 52.0)

def starts_off(story, idx):
    """Characters whose first direction (before the next spoken line / scene) is 'enters' begin off stage."""
    first = {}
    for ev in story[idx:]:
        if isinstance(ev, (Say, SceneChange)): break
        if isinstance(ev, Direction):
            try: ops = parse_dir(ev.text, ev.line)
            except ScriptError: continue
            for op in ops:
                if op.who and op.who not in first: first[op.who] = op.verb
    return {n for n, v in first.items() if v == "enter"}

def play(script, say_seconds, t0=2.6):
    """Run the story through a Stage. say_seconds(ev) -> seconds a line takes. Returns (stage, timeline items, end time)."""
    story = script.story
    scene = SC.resolve(script.meta.get("scene", "street"))
    if not scene: raise ScriptError(f"unknown scene {script.meta.get('scene')!r}; scenes: {', '.join(SC.SCENES)}")
    stage = Stage(scene, starts_off(story, 0)); t = t0; out = []; i = 0
    while i < len(story):
        ev = story[i]
        if isinstance(ev, SceneChange):
            sc = SC.resolve(ev.place)
            if not sc: raise ScriptError(f"line {ev.line}: unknown scene {ev.place!r}. Scenes: {', '.join(SC.SCENES)}")
            stage.cut(t, sc, starts_off(story, i + 1)); out.append(("scene", t, t, sc)); i += 1
        elif isinstance(ev, Direction):
            beats = []
            while i < len(story) and isinstance(story[i], Direction):
                d = story[i]; ops = parse_dir(d.text, d.line)
                if d.simultaneous and beats: beats[-1].extend(ops)
                else: beats.append(list(ops))
                i += 1
            for ops in beats:
                end = stage.run_beat(t, ops); out.append(("act", t, end + 0.2, stage.scene)); t = end + 0.2
        else:
            dur = say_seconds(ev); out.append(("say", t, t + dur + 0.75, ev, stage.scene)); t += dur + 0.75; i += 1
    return stage, out, t

def check(script):
    """Dry run with fake durations: raises ScriptError for anything unsupported."""
    play(script, lambda ev: 2.0)
