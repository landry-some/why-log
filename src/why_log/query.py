"""Filtering journal entries for `list` and `export`."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path

from .journal import Entry

_UNITS = {"m": "minutes", "h": "hours", "d": "days", "w": "weeks"}


def parse_since(text: str, now: datetime | None = None) -> datetime:
    """Turn '30m', '12h', '7d', '2w' or a date like '2026-10-01' into a cutoff time."""
    now = now or datetime.now().astimezone()
    match = re.fullmatch(r"(\d+)([mhdw])", text.strip())
    if match:
        amount, unit = match.groups()
        return now - timedelta(**{_UNITS[unit]: int(amount)})
    try:
        when = datetime.fromisoformat(text.strip())
    except ValueError:
        raise ValueError(
            f"can't read --since {text!r}: use 30m, 12h, 7d, 2w or a date like 2026-10-01"
        ) from None
    if when.tzinfo is None:
        when = when.astimezone()  # a plain date means local time
    return when


def _is_within(path: str, folder: Path) -> bool:
    try:
        Path(path).relative_to(folder)
    except ValueError:
        return False
    return True


def filter_entries(
    entries: list[Entry],
    *,
    grep: str | None = None,
    here: Path | None = None,
    since: datetime | None = None,
    failed: bool = False,
    tag: str | None = None,
    last: int | None = None,
) -> list[Entry]:
    """Keep entries matching every given filter, oldest first.

    grep matches the command or the reason, case-insensitively.
    here keeps entries run in that folder or below it.
    tag keeps entries carrying exactly that tag.
    last keeps only the newest N of the matches.
    """
    needle = grep.lower() if grep else None
    kept = []
    for entry in entries:
        if needle and needle not in entry.cmd.lower() and needle not in entry.why.lower():
            continue
        if here is not None and not _is_within(entry.cwd, here):
            continue
        if since is not None and entry.when < since:
            continue
        if failed and not entry.exit:  # None (added) and 0 both count as not failed
            continue
        if tag is not None and tag not in entry.tags:
            continue
        kept.append(entry)
    if last is not None:
        kept = kept[-last:] if last > 0 else []
    return kept
