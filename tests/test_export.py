import json
import time

import pytest

from why_log.cli import format_status, main
from why_log.export import to_markdown
from why_log.journal import Entry


@pytest.fixture(autouse=True)
def utc(monkeypatch):
    monkeypatch.setenv("TZ", "UTC")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


def entry(id, cmd, why="", time="2026-11-01T10:00:00+00:00", exit=0, duration=1.0, cwd="/srv"):
    return Entry(id=id, time=time, cwd=cwd, cmd=cmd, why=why, exit=exit, duration=duration)


def render(entries, title="Command journal"):
    return to_markdown(entries, title=title, status=format_status, place=lambda p: p)


def test_groups_entries_by_day():
    text = render([
        entry(1, "make", why="build", time="2026-11-01T10:00:00+00:00"),
        entry(2, "make test", time="2026-11-01T11:30:00+00:00", exit=1),
        entry(3, "git push", time="2026-11-02T09:05:00+00:00", exit=None, duration=None),
    ])
    assert text == (
        "# Command journal\n"
        "\n"
        "## 2026-11-01\n"
        "\n"
        "- **10:00** in `/srv` (ok, 1.0s): build\n"
        "\n"
        "  ```sh\n"
        "  make\n"
        "  ```\n"
        "\n"
        "- **11:30** in `/srv` (exit 1, 1.0s)\n"
        "\n"
        "  ```sh\n"
        "  make test\n"
        "  ```\n"
        "\n"
        "## 2026-11-02\n"
        "\n"
        "- **09:05** in `/srv` (added)\n"
        "\n"
        "  ```sh\n"
        "  git push\n"
        "  ```\n"
    )


def test_empty_export_says_so():
    assert render([], title="Deploys") == "# Deploys\n\nNo entries.\n"


def test_commands_with_backticks_get_a_longer_fence():
    text = render([entry(1, "echo ```hi```")])
    assert "  ````sh\n  echo ```hi```\n  ````\n" in text


def test_export_command_applies_filters_and_writes_file(tmp_path, monkeypatch, capsys):
    journal = tmp_path / "j.jsonl"
    journal.write_text(
        json.dumps(dict(id=1, time="2026-11-01T10:00:00+00:00", cwd="/srv", cmd="kubectl apply",
                        why="deploy", exit=0, duration=2.0)) + "\n"
        + json.dumps(dict(id=2, time="2026-11-01T10:05:00+00:00", cwd="/srv", cmd="ls",
                          why="", exit=0, duration=0.1)) + "\n"
    )
    out = tmp_path / "deploys.md"
    code = main(["--file", str(journal), "export", "-g", "deploy", "--title", "Deploys", "-o", str(out)])

    assert code == 0
    assert capsys.readouterr().out == ""
    text = out.read_text()
    assert text.startswith("# Deploys\n")
    assert "kubectl apply" in text and "  ls\n" not in text


def test_tags_follow_the_status():
    e = entry(1, "make deploy", why="ship it")
    e.tags = ["deploy"]
    assert "- **10:00** in `/srv` (ok, 1.0s) [deploy]: ship it\n" in render([e])
