from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from why_log.journal import Entry
from why_log.query import filter_entries, parse_since

NOW = datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc)


def make(id, cmd="ls", why="", cwd="/home/me", exit=0, ago=timedelta(0)):
    when = (NOW - ago).isoformat(timespec="seconds")
    return Entry(id=id, time=when, cwd=cwd, cmd=cmd, why=why, exit=exit)


@pytest.mark.parametrize(
    "text, delta",
    [("30m", timedelta(minutes=30)), ("12h", timedelta(hours=12)),
     ("7d", timedelta(days=7)), ("2w", timedelta(weeks=2))],
)
def test_parse_since_relative(text, delta):
    assert parse_since(text, now=NOW) == NOW - delta


def test_parse_since_date_with_offset():
    assert parse_since("2026-10-01T00:00:00+00:00") == datetime(2026, 10, 1, tzinfo=timezone.utc)


def test_parse_since_plain_date_is_local_and_aware():
    assert parse_since("2026-10-01").tzinfo is not None


def test_parse_since_rejects_garbage():
    with pytest.raises(ValueError, match="7d"):
        parse_since("last tuesday")


def test_grep_matches_command_or_reason_ignoring_case():
    entries = [make(1, cmd="docker prune"), make(2, why="free Docker space"), make(3)]
    assert [e.id for e in filter_entries(entries, grep="DOCKER")] == [1, 2]


def test_here_keeps_folder_and_subfolders_only():
    entries = [
        make(1, cwd="/home/me/proj"),
        make(2, cwd="/home/me/proj/src"),
        make(3, cwd="/home/me/project-two"),
        make(4, cwd="/home/me"),
    ]
    assert [e.id for e in filter_entries(entries, here=Path("/home/me/proj"))] == [1, 2]


def test_since_drops_older_entries():
    entries = [make(1, ago=timedelta(days=10)), make(2, ago=timedelta(days=1))]
    cutoff = NOW - timedelta(days=7)
    assert [e.id for e in filter_entries(entries, since=cutoff)] == [2]


def test_failed_skips_success_and_added_entries():
    entries = [make(1, exit=0), make(2, exit=1), make(3, exit=None), make(4, exit=130)]
    assert [e.id for e in filter_entries(entries, failed=True)] == [2, 4]


def test_last_keeps_newest_matches():
    entries = [make(i) for i in range(1, 6)]
    assert [e.id for e in filter_entries(entries, last=2)] == [4, 5]
    assert filter_entries(entries, last=0) == []


def test_filters_combine():
    entries = [
        make(1, cmd="make", exit=2, cwd="/a"),
        make(2, cmd="make", exit=2, cwd="/b"),
        make(3, cmd="make", exit=0, cwd="/a"),
    ]
    got = filter_entries(entries, grep="make", here=Path("/a"), failed=True)
    assert [e.id for e in got] == [1]


def test_tag_keeps_entries_with_that_tag():
    entries = [make(1), make(2), make(3)]
    entries[0].tags = ["deploy", "prod"]
    entries[2].tags = ["deploy-staging"]
    assert [e.id for e in filter_entries(entries, tag="deploy")] == [1]
