import datetime as dt, json, os, sys
import pytest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import queue_tool as qt

U = dt.timezone.utc
def T(*a): return dt.datetime(*a, tzinfo=U)


def test_slots_are_filled_in_order_with_gaps_and_daily_cap():
    now = T(2026, 10, 25, 18, 0)
    taken = []
    got = []
    for _ in range(4):
        s = qt.next_slot(now, taken); got.append(s); taken.append(s)
    assert got == [T(2026, 10, 26, 1, 0), T(2026, 10, 26, 14, 0), T(2026, 10, 27, 1, 0), T(2026, 10, 27, 14, 0)]


def test_lead_time_skips_a_slot_that_is_too_close():
    assert qt.next_slot(T(2026, 10, 26, 0, 45), []) == T(2026, 10, 26, 14, 0)
    assert qt.next_slot(T(2026, 10, 26, 0, 20), []) == T(2026, 10, 26, 1, 0)


def test_taken_slot_and_minimum_gap_are_respected():
    now = T(2026, 10, 26, 3, 0)
    assert qt.next_slot(now, [T(2026, 10, 26, 14, 0)]) == T(2026, 10, 27, 1, 0)
    cfg = dict(qt.DEFAULTS, slots_utc=["14:00", "18:00"], max_per_day=3)
    assert qt.next_slot(now, [T(2026, 10, 26, 14, 0)], cfg) == T(2026, 10, 27, 14, 0)


def _media(tmp_path, stem="lesson"):
    d = tmp_path / "media"; d.mkdir()
    (d / f"{stem}.mp4").write_bytes(b"0" * 100); (d / f"{stem}.jpg").write_bytes(b"1"); (d / f"{stem}.srt").write_text("x")
    (d / f"{stem}.caption.txt").write_text("Bonjour 🇫🇷", encoding="utf-8"); (d / f"{stem}.json").write_text(json.dumps({"title": "Mon titre é"}), encoding="utf-8")
    return str(d)


def test_add_due_done_and_fail_flow(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(qt, "QUEUE", str(tmp_path / "queue"))
    os.makedirs(qt.QUEUE)
    media = _media(tmp_path)
    qt.main(["add", "--stem", "lesson", "--media-dir", media, "--format", "small"])
    e = json.load(open(os.path.join(qt.QUEUE, "lesson.json"), encoding="utf-8"))
    assert e["status"] == "pending" and e["title"] == "Mon titre é" and e["post_at"].endswith("Z")
    assert os.path.exists(os.path.join(qt.QUEUE, "videos", "lesson.mp4"))
    capsys.readouterr(); qt.main(["due"]); assert capsys.readouterr().out.strip() == ""      # in the future
    e["post_at"] = "2020-01-01T00:00:00Z"; json.dump(e, open(os.path.join(qt.QUEUE, "lesson.json"), "w"))
    qt.main(["due"]); assert capsys.readouterr().out.split() == ["lesson"]
    for _ in range(3): qt.main(["fail", "--stem", "lesson"])
    capsys.readouterr(); qt.main(["due"]); assert capsys.readouterr().out.strip() == ""      # gave up after 3 attempts
    e = json.load(open(os.path.join(qt.QUEUE, "lesson.json"))); assert e["status"] == "failed"
    e.update(status="pending", attempts=0); json.dump(e, open(os.path.join(qt.QUEUE, "lesson.json"), "w"))
    qt.main(["done", "--stem", "lesson", "--media-id", "123"])
    assert not os.path.exists(os.path.join(qt.QUEUE, "lesson.json")) and not os.path.exists(os.path.join(qt.QUEUE, "videos", "lesson.mp4"))
    d = json.load(open(os.path.join(qt.QUEUE, "done", "lesson.json"))); assert d["status"] == "posted" and d["media_id"] == "123"


def test_second_video_gets_a_later_slot(tmp_path, monkeypatch):
    monkeypatch.setattr(qt, "QUEUE", str(tmp_path / "queue")); os.makedirs(qt.QUEUE)
    qt.main(["add", "--stem", "a", "--media-dir", _media(tmp_path, "a")])
    (tmp_path / "media").rename(tmp_path / "media_a")
    qt.main(["add", "--stem", "b", "--media-dir", _media(tmp_path, "b")])
    a = json.load(open(os.path.join(qt.QUEUE, "a.json")))["post_at"]; b = json.load(open(os.path.join(qt.QUEUE, "b.json")))["post_at"]
    assert qt.parse(b) - qt.parse(a) >= dt.timedelta(hours=8)


def test_add_without_a_video_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(qt, "QUEUE", str(tmp_path / "queue")); os.makedirs(qt.QUEUE)
    (tmp_path / "m").mkdir()
    with pytest.raises(SystemExit):
        qt.main(["add", "--stem", "x", "--media-dir", str(tmp_path / "m")])
