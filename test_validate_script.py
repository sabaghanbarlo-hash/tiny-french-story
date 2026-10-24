import os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GOOD = open(os.path.join(HERE, "lessons", "03-un-croissant.txt"), encoding="utf-8").read()


def run(text):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(text)
    try:
        return subprocess.run([sys.executable, os.path.join(HERE, "validate_script.py"), f.name], capture_output=True, text=True, encoding="utf-8")
    finally:
        os.unlink(f.name)


def test_good_script_passes_with_accents():
    r = run(GOOD)
    assert r.returncode == 0, r.stdout
    assert "Script OK" in r.stdout


def test_empty_script_fails():
    r = run("  \n")
    assert r.returncode == 1 and "::error" in r.stdout


def test_too_long_fails():
    r = run(GOOD + "\n# " + "x" * 21000)
    assert r.returncode == 1 and "too long" in r.stdout


def test_unknown_scene_fails_with_message():
    r = run(GOOD.replace("@scene bakery", "@scene moon-base"))
    assert r.returncode == 1 and "::error" in r.stdout
    assert "\n" not in r.stdout.strip().split("::error title=Script problem::")[-1]
