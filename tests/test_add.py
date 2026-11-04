import pytest

from why_log.cli import main
from why_log.journal import read_entries


@pytest.fixture
def journal(tmp_path, monkeypatch):
    path = tmp_path / "journal.jsonl"
    monkeypatch.setenv("WHYLOG_FILE", str(path))
    monkeypatch.chdir(tmp_path)
    return path


def test_add_records_quoted_command_without_running_it(journal, tmp_path, capsys):
    code = main(["add", "-m", "freed 20 GB", "docker system prune -a"])

    assert code == 0
    assert capsys.readouterr().out == "recorded #1\n"
    [entry] = read_entries(journal)
    assert entry.cmd == "docker system prune -a"
    assert entry.why == "freed 20 GB"
    assert entry.cwd == str(tmp_path)
    assert entry.exit is None
    assert entry.duration is None


def test_add_joins_unquoted_words(journal):
    main(["add", "-m", "x", "git", "gc", "--aggressive"])
    assert read_entries(journal)[0].cmd == "git gc --aggressive"


def test_add_accepts_known_exit_code(journal):
    main(["add", "--exit", "1", "make test"])
    assert read_entries(journal)[0].exit == 1


def test_add_ids_continue_after_run_entries(journal):
    main(["add", "first"])
    main(["add", "second"])
    assert [e.id for e in read_entries(journal)] == [1, 2]


def test_add_rejects_blank_command(journal, capsys):
    assert main(["add", "  "]) == 2
    assert not journal.exists()


def test_add_strips_double_dash(journal):
    main(["add", "-m", "x", "--", "ls", "-la"])
    assert read_entries(journal)[0].cmd == "ls -la"


def test_add_without_command_is_a_usage_error(journal):
    assert main(["add", "-m", "x"]) == 2


def test_add_records_tags(journal):
    main(["add", "-t", "deploy", "--tag", "prod", "-m", "x", "make deploy"])
    assert read_entries(journal)[0].tags == ["deploy", "prod"]


def test_add_without_tags_stores_empty_list(journal):
    main(["add", "ls"])
    assert read_entries(journal)[0].tags == []
