"""Script parser for Tiny French lessons (UTF-8, accents preserved)."""
import re
from dataclasses import dataclass, field
from .config import CHARS

class ScriptError(Exception):
    pass

@dataclass
class Say:
    speaker: str; fr: str; en: str; hint: str; line: int
@dataclass
class Direction:
    text: str; simultaneous: bool; line: int
@dataclass
class SceneChange:
    place: str; line: int
@dataclass
class Vocab:
    term: str; meaning: str; examples: list = field(default_factory=list)   # [(fr, en or "")]
@dataclass
class Grammar:
    pattern: str; meaning: str; examples: list = field(default_factory=list)
@dataclass
class Quiz:
    question: str; options: dict; answer: str; explanation: str
@dataclass
class Script:
    meta: dict; story: list; vocab: list; grammar: list; quiz: list

SECTION = re.compile(r"^\[(story|vocab|grammar|quiz)\]\s*$", re.I)
SAY = re.compile(r"^(" + "|".join(CHARS) + r")\s*:\s*(.+)$")
SEP = re.compile(r"\s+[\u2014\u2013]\s+|\s+-\s+|\s+=\s+")
OPT = re.compile(r"^([A-D])[).]\s*(.+)$")
EX = re.compile(r"^Example(?:\s*\d+)?\s*:\s*(.+)$", re.I)

def _clean(s):
    return s.strip()

def _unquote(line):
    """Tolerate stray guillemets wrapped around a whole line (copy/paste artefact)."""
    s = line.strip()
    if s.startswith("\u00ab") and (SAY.match(s[1:].strip()) or s[1:].lstrip().startswith((">", "&", "@"))):
        s = s[1:].strip()
    if s.endswith("\u00bb") and "\u00ab" not in s:
        s = s[:-1].rstrip()
    return s

def _split_fr_en(text, ln):
    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 2 or not parts[0] or not parts[1]:
        raise ScriptError(f"line {ln}: spoken line needs 'French | English' (missing translation): {text!r}")
    return parts[0], parts[1], (parts[2] if len(parts) > 2 else "")

def parse_script(text):
    lines = text.replace("\ufeff", "").splitlines()
    meta, sec, buf = {}, None, {"story": [], "vocab": [], "grammar": [], "quiz": []}
    for i, raw in enumerate(lines, 1):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        m = SECTION.match(s)
        if m:
            sec = m.group(1).lower(); continue
        if sec is None:
            if ":" not in s:
                raise ScriptError(f"line {i}: header lines look like 'title: ...' (got {s!r})")
            k, v = s.split(":", 1); meta[k.strip().lower()] = v.strip(); continue
        buf[sec].append((i, raw.rstrip()))
    if not meta.get("title"):
        raise ScriptError("missing 'title:' in the header")
    for need in ("story", "vocab", "grammar", "quiz"):
        if not buf[need]:
            raise ScriptError(f"missing or empty [{need}] section")
    story = _parse_story(buf["story"])
    if not any(isinstance(e, Say) for e in story):
        raise ScriptError("[story] has no spoken lines")
    return Script(meta, story, _parse_vocab(buf["vocab"]), _parse_grammar(buf["grammar"]), _parse_quiz(buf["quiz"]))

def _parse_story(items):
    out = []
    for ln, raw in items:
        s = _unquote(raw)
        if s.startswith("@scene"):
            place = s[6:].strip()
            if not place:
                raise ScriptError(f"line {ln}: '@scene' needs a place name")
            out.append(SceneChange(place.lower(), ln)); continue
        if s.startswith(">"):
            out.append(Direction(s[1:].strip(), False, ln)); continue
        if s.startswith("&"):
            out.append(Direction(s[1:].strip(), True, ln)); continue
        m = SAY.match(s)
        if m:
            fr, en, hint = _split_fr_en(m.group(2), ln)
            out.append(Say(m.group(1), fr, en, hint, ln)); continue
        if re.match(r"^\w+\s*:", s):
            who = s.split(":", 1)[0]
            raise ScriptError(f"line {ln}: unknown speaker {who!r}; speakers are {', '.join(CHARS)}")
        raise ScriptError(f"line {ln}: not a spoken line or direction (directions must start with '>' or '&'): {s!r}")
    return out

def _entries(items, kind):
    cur, out = None, []
    for ln, raw in items:
        s = raw.strip()
        if s.startswith(("- ", "* ")):
            body = s[2:].strip()
            parts = SEP.split(body, maxsplit=1)
            if len(parts) < 2:
                raise ScriptError(f"line {ln}: [{kind}] entry needs 'item \u2014 meaning': {s!r}")
            cur = dict(a=_clean(parts[0]), b=_clean(parts[1]), ex=[]); out.append(cur); continue
        m = EX.match(s)
        if m and cur is not None:
            fr, _, en = m.group(1).partition("|")
            cur["ex"].append((fr.strip(), en.strip())); continue
        raise ScriptError(f"line {ln}: unexpected line in [{kind}]: {s!r}")
    return out

def _parse_vocab(items):
    out = [Vocab(e["a"], e["b"], e["ex"]) for e in _entries(items, "vocab")]
    if not out: raise ScriptError("[vocab] is empty")
    return out

def _parse_grammar(items):
    out = [Grammar(e["a"], e["b"], e["ex"]) for e in _entries(items, "grammar")]
    if not out: raise ScriptError("[grammar] is empty")
    return out

def _parse_quiz(items):
    out, cur = [], None
    def close():
        if cur is None: return
        if len(cur["options"]) < 2: raise ScriptError(f"quiz question {cur['q']!r} needs at least 2 options")
        if cur["answer"] not in cur["options"]: raise ScriptError(f"quiz question {cur['q']!r}: Answer must be one of {sorted(cur['options'])}")
        out.append(Quiz(cur["q"], cur["options"], cur["answer"], cur["exp"]))
    for ln, raw in items:
        s = raw.strip()
        if s.upper().startswith("Q:"):
            close(); cur = dict(q=s[2:].strip(), options={}, answer=None, exp="")
        elif cur is None:
            raise ScriptError(f"line {ln}: [quiz] must start with 'Q:'")
        elif OPT.match(s):
            m = OPT.match(s); cur["options"][m.group(1)] = m.group(2).strip()
        elif s.lower().startswith("answer:"):
            cur["answer"] = s.split(":", 1)[1].strip().upper()[:1]
        elif s.lower().startswith("explanation:"):
            cur["exp"] = s.split(":", 1)[1].strip()
        else:
            raise ScriptError(f"line {ln}: unexpected line in [quiz]: {s!r}")
    close()
    if not out: raise ScriptError("[quiz] has no questions")
    return out
