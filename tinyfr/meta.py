"""Instagram caption (UTF-8 text, <= 2200 chars) generated from the lesson itself."""
HASHTAGS = ["#learnfrench", "#frenchforbeginners", "#french", "#frenchlanguage", "#frenchlesson", "#apprendrelefrançais", "#languagelearning", "#tinyfrench"]
LIMIT = 2200

def caption(script):
    m = script.meta; lines = [f"Learn French with Marinette & Adrien 🇫🇷 — {m['title']}", ""]
    lines.append("Today's tiny French:")
    for v in script.vocab[:5]:
        lines.append(f"• {v.term} — {v.meaning}")
    if script.grammar:
        g = script.grammar[0]; lines += ["", f"Pattern: {g.pattern} — {g.meaning}"]
        if g.examples: lines.append(f"e.g. {g.examples[0][0]}")
    if script.quiz: lines += ["", "Can you answer the quiz at the end? Tell us in the comments 👇"]
    lines += ["Small steps. Big dreams.", "", " ".join(HASHTAGS)]
    text = "\n".join(lines)
    if len(text) > LIMIT: text = text[:LIMIT - 1] + "…"
    return text

def write_caption(script, path):
    with open(path, "w", encoding="utf-8", newline="\n") as f: f.write(caption(script) + "\n")
