import os
import shlex
import sys

import pytest

from why_log.cli import main
from why_log.journal import read_entries

PY = sys.executable


@pytest.fixture
def journal(tmp_path, monkeypatch):
    path = tmp_path / "journal.jsonl"
    monkeypatch.setenv("WHYLOG_FILE", str(path))
    monkeypatch.chdir(tmp_path)
    return path


def test_run_records_command_reason_dir_and_exit(journal, tmp_path):
    code = main(["run", "-m", "check python", "--", PY, "-c", "print('hi')"])

    assert code == 0
    [entry] = read_entries(journal)
    assert entry.cmd == shlex.join([PY, "-c", "print('hi')"])
    assert entry.why == "check python"
    assert entry.cwd == str(tmp_path)
    assert entry.exit == 0
    assert entry.duration >= 0


def test_run_passes_exit_code_through(journal):
    code = main(["run", "--", PY, "-c", "raise SystemExit(3)"])
    assert code == 3
    assert read_entries(journal)[0].exit == 3


def test_run_lets_output_reach_the_terminal(journal, capfd):
    main(["run", "--", PY, "-c", "print('visible')"])
    assert "visible" in capfd.readouterr().out


def test_run_records_missing_command_as_127(journal, capsys):
    code = main(["run", "-m", "typo", "--", "no-such-command-xyz"])
    assert code == 127
    assert "command not found" in capsys.readouterr().err
    assert read_entries(journal)[0].exit == 127


def test_run_without_command_is_a_usage_error(journal, capsys):
    assert main(["run", "-m", "nothing"]) == 2
    assert not journal.exists()


def test_run_accepts_command_without_double_dash(journal):
    assert main(["run", PY, "-c", "pass"]) == 0
    assert read_entries(journal)[0].cmd.endswith("-c pass")


@pytest.mark.skipif(os.name != "posix", reason="signals")
def test_run_maps_signal_death_to_128_plus_n(journal):
    code = main(["run", "--", PY, "-c", "import os, signal; os.kill(os.getpid(), signal.SIGTERM)"])
    assert code == 128 + 15


def test_file_option_overrides_env(journal, tmp_path):
    other = tmp_path / "other.jsonl"
    main(["--file", str(other), "run", "--", PY, "-c", "pass"])
    assert len(read_entries(other)) == 1
    assert not journal.exists()


def test_run_records_tags(journal):
    main(["run", "-t", "check", "--", PY, "-c", "pass"])
    assert read_entries(journal)[0].tags == ["check"]
