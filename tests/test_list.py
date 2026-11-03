import json
import time

import pytest

from why_log.cli import main


@pytest.fixture
def journal(tmp_path, monkeypatch):
    path = tmp_path / "journal.jsonl"
    monkeypatch.setenv("WHYLOG_FILE", str(path))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("TZ", "UTC")
    time.tzset()
    monkeypatch.chdir(tmp_path)
    yield path
    monkeypatch.undo()
    time.tzset()


def write(path, *entries):
    with path.open("w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


def entry(id, cmd, why="", cwd="/srv", exit=0, duration=0.5, time="2026-11-01T10:00:00+00:00"):
    return dict(id=id, time=time, cwd=cwd, cmd=cmd, why=why, exit=exit, duration=duration)


def test_list_empty_journal_prints_nothing(journal, capsys):
    assert main(["list"]) == 0
    assert capsys.readouterr().out == ""


def test_list_shows_each_entry_as_a_block(journal, capsys):
    write(
        journal,
        entry(1, "make deploy", why="ship 1.2", exit=0, duration=12.34),
        entry(2, "tar xzf a.tgz", exit=None, duration=None),
    )
    main(["list"])
    assert capsys.readouterr().out == (
        "#1  2026-11-01 10:00  ok, 12.3s  /srv\n"
        "    $ make deploy\n"
        "    why: ship 1.2\n"
        "\n"
        "#2  2026-11-01 10:00  added  /srv\n"
        "    $ tar xzf a.tgz\n"
    )


def test_list_shows_failure_exit_code(journal, capsys):
    write(journal, entry(1, "pytest", exit=1, duration=3))
    main(["list"])
    assert "exit 1, 3.0s" in capsys.readouterr().out


def test_list_shortens_home_to_tilde(journal, tmp_path, capsys):
    write(journal, entry(1, "ls", cwd=str(tmp_path / "proj")))
    main(["list"])
    assert "  ~/proj\n" in capsys.readouterr().out


def test_list_filters_from_command_line(journal, tmp_path, capsys):
    write(
        journal,
        entry(1, "make", exit=2, cwd=str(tmp_path)),
        entry(2, "make", exit=0, cwd=str(tmp_path)),
        entry(3, "make", exit=2, cwd="/elsewhere"),
        entry(4, "ls", exit=2, cwd=str(tmp_path)),
    )
    main(["ls", "--grep", "make", "--here", "--failed"])
    out = capsys.readouterr().out
    assert "#1 " in out
    assert "#2 " not in out and "#3 " not in out and "#4 " not in out


def test_list_last_n(journal, capsys):
    write(journal, *(entry(i, f"cmd{i}") for i in range(1, 6)))
    main(["list", "-n", "2"])
    out = capsys.readouterr().out
    assert "cmd3" not in out and "cmd4" in out and "cmd5" in out


def test_list_since_date(journal, capsys):
    write(
        journal,
        entry(1, "old", time="2026-09-01T10:00:00+00:00"),
        entry(2, "new", time="2026-11-01T10:00:00+00:00"),
    )
    main(["list", "--since", "2026-10-01"])
    out = capsys.readouterr().out
    assert "new" in out and "old" not in out


def test_list_bad_since_is_a_usage_error(journal, capsys):
    assert main(["list", "--since", "yesterday-ish"]) == 2
    assert "can't read --since" in capsys.readouterr().err
