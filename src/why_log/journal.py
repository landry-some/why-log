"""Reading and writing the journal file.

The journal is a JSON Lines file: one entry per line, appended in order.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Entry:
    id: int
    time: str  # ISO 8601 with UTC offset
    cwd: str
    cmd: str
    why: str
    exit: int | None = None  # None when the command was added, not run
    duration: float | None = None  # seconds
    tags: list[str] = field(default_factory=list)

    @property
    def when(self) -> datetime:
        return datetime.fromisoformat(self.time)


def default_path() -> Path:
    """Journal location: $WHYLOG_FILE, else $XDG_DATA_HOME/why-log/journal.jsonl."""
    env = os.environ.get("WHYLOG_FILE")
    if env:
        return Path(env).expanduser()
    data_home = os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share"
    return Path(data_home) / "why-log" / "journal.jsonl"


def _parse_line(line: str) -> Entry:
    """Turn one journal line into an Entry. Raises ValueError if it isn't one."""
    data = json.loads(line)  # JSONDecodeError is a ValueError
    if not isinstance(data, dict):
        raise ValueError("not a JSON object")
    try:
        entry = Entry(**data)
    except TypeError as err:  # missing or unknown fields
        raise ValueError(str(err).removeprefix("Entry.__init__() ")) from None
    datetime.fromisoformat(entry.time)  # fail here, not later while listing
    return entry


def read_entries(path: Path) -> list[Entry]:
    """Read all entries. Corrupt lines are skipped with a warning on stderr."""
    if not path.exists():
        return []
    entries = []
    with path.open(encoding="utf-8", errors="replace") as f:
        for number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(_parse_line(line))
            except ValueError as err:
                print(f"whylog: skipping corrupt line {number} in {path}: {err}", file=sys.stderr)
    return entries


def append_entry(
    path: Path,
    *,
    cmd: str,
    why: str,
    cwd: str,
    time: datetime | None = None,
    exit: int | None = None,
    duration: float | None = None,
    tags: list[str] | None = None,
) -> Entry:
    """Append a new entry with the next free id and return it."""
    existing = read_entries(path)
    next_id = max((e.id for e in existing), default=0) + 1
    when = time or datetime.now().astimezone()
    entry = Entry(
        id=next_id,
        time=when.isoformat(timespec="seconds"),
        cwd=cwd,
        cmd=cmd,
        why=why,
        exit=exit,
        duration=None if duration is None else round(duration, 3),
        tags=list(tags or []),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
    return entry
