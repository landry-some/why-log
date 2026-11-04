"""Markdown export of journal entries."""

from __future__ import annotations

import re
from collections.abc import Callable

from .journal import Entry


def _fence(text: str) -> str:
    """A backtick fence longer than any backtick run inside text."""
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def to_markdown(entries: list[Entry], *, title: str, status: Callable[[Entry], str],
                place: Callable[[str], str]) -> str:
    """Render entries grouped by local date, one bullet and code block per command."""
    lines = [f"# {title}"]
    current_day = None
    for entry in entries:
        when = entry.when.astimezone()
        day = when.strftime("%Y-%m-%d")
        if day != current_day:
            lines += ["", f"## {day}"]
            current_day = day
        head = f"- **{when:%H:%M}** in `{place(entry.cwd)}` ({status(entry)})"
        if entry.tags:
            head += f" [{', '.join(entry.tags)}]"
        if entry.why:
            head += f": {entry.why}"
        fence = _fence(entry.cmd)
        lines += ["", head, "", f"  {fence}sh"]
        lines += [f"  {line}" for line in entry.cmd.splitlines() or [""]]
        lines.append(f"  {fence}")
    if not entries:
        lines += ["", "No entries."]
    return "\n".join(lines) + "\n"
