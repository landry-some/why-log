import pytest

from why_log.cli import main
from why_log.journal import append_entry, read_entries, rewrite_entry


@pytest.fixture
def journal(tmp_path, monkeypatch):
    path = tmp_path / "journal.jsonl"
    monkeypatch.setenv("WHYLOG_FILE", str(path))
    monkeypatch.chdir(tmp_path)
    for cmd in ("ls", "make", "git push"):
        append_entry(path, cmd=cmd, why=f"why {cmd}", cwd="/srv", exit=0, duration=1.0, tags=["t"])
    return path


def test_edit_changes_only_the_reason(journal, capsys):
    before = read_entries(journal)
    assert main(["edit", "2", "-m", "build the docs, not the app"]) == 0
    assert capsys.readouterr().out == "updated #2\n"

    after = read_entries(journal)
    assert after[1].why == "build the docs, not the app"
    assert after[1].cmd == "make" and after[1].tags == ["t"] and after[1].time == before[1].time
    assert [after[0], after[2]] == [before[0], before[2]]


def test_rm_drops_the_entry_and_keeps_order(journal, capsys):
    assert main(["rm", "2"]) == 0
    assert capsys.readouterr().out == "removed #2\n"
    assert [e.id for e in read_entries(journal)] == [1, 3]


def test_ids_keep_counting_after_rm(journal):
    main(["rm", "2"])
    main(["add", "new"])
    assert [e.id for e in read_entries(journal)] == [1, 3, 4]


@pytest.mark.parametrize("argv", [["edit", "9", "-m", "x"], ["rm", "9"]])
def test_unknown_id_is_an_error(journal, capsys, argv):
    before = journal.read_text()
    assert main(argv) == 1
    assert "no entry #9" in capsys.readouterr().err
    assert journal.read_text() == before


def test_rm_on_missing_journal_is_an_error(tmp_path, capsys):
    assert main(["--file", str(tmp_path / "none.jsonl"), "rm", "1"]) == 1
    assert not (tmp_path / "none.jsonl").exists()


def test_edit_requires_a_message(journal):
    with pytest.raises(SystemExit):
        main(["edit", "1"])


def test_rewrite_keeps_corrupt_and_blank_lines(journal, capsys):
    with journal.open("a") as f:
        f.write("\nnot json at all\n")
    append_entry(journal, cmd="last", why="", cwd="/")

    assert rewrite_entry(journal, 1, None)
    lines = journal.read_text().splitlines()
    assert "not json at all" in lines and "" in lines
    assert not (journal.parent / "journal.jsonl.tmp").exists()
    assert [e.id for e in read_entries(journal)] == [2, 3, 4]
