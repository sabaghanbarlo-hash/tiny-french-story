"""Instagram caption (UTF-8 text, <= 2200 chars) generated from the lesson itself."""
HASHTAGS = ["#learnfrench", "#frenchforbeginners", "#french", "#frenchlanguage", "#frenchlesson", "#apprendrelefrançais", "#languagelearning", "#tinyfrench"]
LIMIT = 2200

import re
_NOTE = re.compile(r"[ \t]*\((?:your|this is your|keep|note|tip|top post|best post)[^)]*\)", re.I)

def clean_caption(text):
    """Drop stray generator notes such as '(Your top post pattern: ...)' so they never reach Instagram."""
    text = _NOTE.sub("", text)
    return re.sub(r"[ \t]+\n", "\n", text).strip()


def caption(script):
    from .acting import cast_of
    m = script.meta; lines = [f"{m['title']} 🇫🇷 Say it like a French person 👇", ""]
    lines.append("Today's tiny French:")
    for v in script.vocab[:5]:
        lines.append(f"• {v.term} — {v.meaning}")
    if script.grammar:
        g = script.grammar[0]; lines += ["", f"Pattern: {g.pattern} — {g.meaning}"]
        if g.examples: lines.append(f"e.g. {g.examples[0][0]}")
    if script.quiz: lines += ["", "Quiz at the end: can you get it? 🧠"]
    lines += ["", "Send this to someone learning French 💌", "Save it to practice later 📌", "", f"Learn French with {' & '.join(cast_of(script)[0][:2])}, one tiny story at a time.", "", " ".join(HASHTAGS)]
    text = "\n".join(lines)
    if len(text) > LIMIT: text = text[:LIMIT - 1] + "…"
    return text

def write_caption(script, path):
    with open(path, "w", encoding="utf-8", newline="\n") as f: f.write(caption(script) + "\n")
