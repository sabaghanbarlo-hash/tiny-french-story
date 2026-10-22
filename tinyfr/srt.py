"""SRT output: French line over English line, UTF-8."""
def ts(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def write_srt(path, cues):
    """cues: [(start, end, french, english)]"""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for i, (a, b, fr, en) in enumerate(cues, 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{fr}\n{en}\n\n")
