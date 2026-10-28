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


# ---- choosing the exact time of a Reel ----
def test_parse_when_understands_the_common_forms():
    want = T(2026, 10, 30, 18, 30)
    for s in ("2026-10-30T18:30Z", "2026-10-30T18:30:00Z", "2026-10-30 18:30", "2026-10-30T18:30", "2026-10-30T22:00:00+03:30"):
        assert qt.parse_when(s) == want, s
    assert qt.fmt(qt.parse_when("2026-10-30T18:30:00-05:00")) == "2026-10-30T23:30:00Z"


@pytest.mark.parametrize("bad", ["", "banana", "2026-10-30", "30/10/2026 18:30", "2026-13-40T18:30Z"])
def test_parse_when_rejects_unreadable_times(bad):
    with pytest.raises(ValueError):
        qt.parse_when(bad)


def test_add_with_your_own_time_uses_exactly_that_time(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(qt, "QUEUE", str(tmp_path / "queue")); os.makedirs(qt.QUEUE)
    when = (qt.utcnow() + dt.timedelta(days=5)).replace(hour=18, minute=37, second=0, microsecond=0)
    qt.main(["add", "--stem", "lesson", "--media-dir", _media(tmp_path), "--post-at", qt.fmt(when)])
    e = json.load(open(os.path.join(qt.QUEUE, "lesson.json"), encoding="utf-8"))
    assert e["post_at"] == qt.fmt(when) and e["scheduled_by"] == "you" and e["status"] == "pending"
    assert "the time you chose" in capsys.readouterr().out


def test_your_own_time_ignores_the_daily_cap_but_later_auto_slots_still_avoid_it(tmp_path, monkeypatch):
    monkeypatch.setattr(qt, "QUEUE", str(tmp_path / "queue")); os.makedirs(qt.QUEUE)
    base = qt.utcnow() + dt.timedelta(days=5)
    mine = [base.replace(hour=h, minute=0, second=0, microsecond=0) for h in (9, 10, 11)]    # 3 posts in one day, 1 hour apart
    for i, w in enumerate(mine):
        (tmp_path / f"m{i}").mkdir()
        d = tmp_path / f"m{i}"; (d / f"v{i}.mp4").write_bytes(b"0")
        qt.main(["add", "--stem", f"v{i}", "--media-dir", str(d), "--post-at", qt.fmt(w)])
    got = sorted(qt.parse(e["post_at"]) for _, e in qt._read(qt.QUEUE))
    assert got == mine


def test_a_time_in_the_past_means_post_at_the_next_check(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(qt, "QUEUE", str(tmp_path / "queue")); os.makedirs(qt.QUEUE)
    qt.main(["add", "--stem", "lesson", "--media-dir", _media(tmp_path), "--post-at", "2020-01-01T00:00Z"])
    e = json.load(open(os.path.join(qt.QUEUE, "lesson.json"), encoding="utf-8"))
    assert qt.utcnow() - qt.parse(e["post_at"]) < dt.timedelta(minutes=1)
    assert "already passed" in capsys.readouterr().out
    qt.main(["due"]); assert capsys.readouterr().out.split()[-1] == "lesson"


def test_add_with_an_unreadable_time_stops_with_a_clear_message(tmp_path, monkeypatch):
    monkeypatch.setattr(qt, "QUEUE", str(tmp_path / "queue")); os.makedirs(qt.QUEUE)
    with pytest.raises(SystemExit) as ex:
        qt.main(["add", "--stem", "lesson", "--media-dir", _media(tmp_path), "--post-at", "tomorrow evening"])
    assert "Can't read the time" in str(ex.value)
    assert not os.path.exists(os.path.join(qt.QUEUE, "lesson.json"))


def test_reschedule_moves_a_waiting_or_failed_reel(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(qt, "QUEUE", str(tmp_path / "queue")); os.makedirs(qt.QUEUE)
    qt.main(["add", "--stem", "lesson", "--media-dir", _media(tmp_path)])
    p = os.path.join(qt.QUEUE, "lesson.json"); e = json.load(open(p)); assert e["scheduled_by"] == "auto"
    e.update(status="failed", attempts=3); json.dump(e, open(p, "w"))
    qt.main(["reschedule", "--stem", "lesson", "--post-at", "2031-05-06 07:08"])
    e = json.load(open(p)); assert (e["post_at"], e["status"], e["attempts"], e["scheduled_by"]) == ("2031-05-06T07:08:00Z", "pending", 0, "you")
    capsys.readouterr(); qt.main(["show"]); assert "time you chose" in capsys.readouterr().out
    with pytest.raises(SystemExit, match="not waiting"):
        qt.main(["reschedule", "--stem", "nope", "--post-at", "2031-05-06 07:08"])
    with pytest.raises(SystemExit, match="Can't read"):
        qt.main(["reschedule", "--stem", "lesson", "--post-at", "whenever"])


def test_when_command_prints_the_utc_time(capsys):
    qt.main(["when", "2026-10-30T22:00+03:30"]); assert capsys.readouterr().out.strip() == "2026-10-30T18:30:00Z"
    with pytest.raises(SystemExit):
        qt.main(["when", "nonsense"])

