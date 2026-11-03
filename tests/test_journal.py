from datetime import datetime, timezone

from why_log.journal import append_entry, default_path, read_entries


def test_missing_file_reads_as_empty(tmp_path):
    assert read_entries(tmp_path / "nope.jsonl") == []


def test_append_creates_parent_dirs_and_numbers_entries(tmp_path):
    path = tmp_path / "deep" / "journal.jsonl"
    first = append_entry(path, cmd="ls", why="look", cwd="/tmp")
    second = append_entry(path, cmd="make", why="build", cwd="/src", exit=2, duration=1.23456)

    assert (first.id, second.id) == (1, 2)
    entries = read_entries(path)
    assert [e.cmd for e in entries] == ["ls", "make"]
    assert entries[1].exit == 2
    assert entries[1].duration == 1.235
    assert entries[0].exit is None


def test_time_is_stored_with_offset(tmp_path):
    path = tmp_path / "j.jsonl"
    when = datetime(2026, 3, 1, 9, 30, tzinfo=timezone.utc)
    entry = append_entry(path, cmd="x", why="", cwd="/", time=when)
    assert entry.time == "2026-03-01T09:30:00+00:00"
    assert read_entries(path)[0].when == when


def test_non_ascii_text_round_trips(tmp_path):
    path = tmp_path / "j.jsonl"
    append_entry(path, cmd="echo café", why="test ünïcode", cwd="/")
    assert read_entries(path)[0].why == "test ünïcode"
    assert "café" in path.read_text(encoding="utf-8")


def test_blank_lines_are_ignored(tmp_path):
    path = tmp_path / "j.jsonl"
    append_entry(path, cmd="a", why="", cwd="/")
    with path.open("a") as f:
        f.write("\n\n")
    append_entry(path, cmd="b", why="", cwd="/")
    assert [e.id for e in read_entries(path)] == [1, 2]


def test_default_path_prefers_whylog_file(monkeypatch, tmp_path):
    monkeypatch.setenv("WHYLOG_FILE", str(tmp_path / "mine.jsonl"))
    assert default_path() == tmp_path / "mine.jsonl"


def test_default_path_uses_xdg_data_home(monkeypatch, tmp_path):
    monkeypatch.delenv("WHYLOG_FILE", raising=False)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert default_path() == tmp_path / "why-log" / "journal.jsonl"
