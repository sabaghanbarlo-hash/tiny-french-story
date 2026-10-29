#!/usr/bin/env python3
"""Check a lesson script with the real parser. Prints GitHub-style errors with line numbers. Exit 1 if invalid."""
import sys
from tinyfr.parser import ScriptError
from tinyfr.autodirect import parse_any
from tinyfr import acting

MAX_CHARS = 20000


def main(path):
    text = open(path, encoding="utf-8").read()
    if not text.strip():
        return fail("The script is empty.")
    if len(text) > MAX_CHARS:
        return fail(f"The script is too long ({len(text)} characters; limit {MAX_CHARS}).")
    try:
        script = parse_any(text)
        acting.check(script)
    except ScriptError as e:
        return fail(str(e))
    print(f"Script OK: {script.meta.get('title', '(untitled)')}")
    return 0


def fail(msg):
    print("::error title=Script problem::" + msg.replace("%", "%25").replace("\r", "").replace("\n", "%0A"))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
