"""Command-line interface for why-log."""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

from . import __version__
from .journal import Entry, append_entry, default_path, read_entries
from .query import filter_entries, parse_since


def run_command(argv: list[str]) -> tuple[int, float]:
    """Run argv with the terminal's stdin/stdout/stderr. Return (exit code, seconds)."""
    start = time.monotonic()
    try:
        code = subprocess.call(argv)
    except FileNotFoundError:
        print(f"whylog: command not found: {argv[0]}", file=sys.stderr)
        code = 127
    except PermissionError:
        print(f"whylog: permission denied: {argv[0]}", file=sys.stderr)
        code = 126
    except KeyboardInterrupt:
        code = 130
    if code < 0:  # killed by a signal: use the shell's 128+N convention
        code = 128 - code
    return code, time.monotonic() - start


def _command_words(words: list[str]) -> list[str]:
    """Drop the optional `--` that separates whylog's options from the command."""
    return words[1:] if words and words[0] == "--" else words


def cmd_run(args: argparse.Namespace) -> int:
    argv = _command_words(args.command)
    if not argv:
        print("whylog run: no command given (usage: whylog run -m WHY -- CMD ...)", file=sys.stderr)
        return 2
    code, seconds = run_command(argv)
    append_entry(
        args.file,
        cmd=shlex.join(argv),
        why=args.message,
        cwd=os.getcwd(),
        exit=code,
        duration=seconds,
    )
    return code


def cmd_add(args: argparse.Namespace) -> int:
    cmd = " ".join(_command_words(args.command)).strip()
    if not cmd:
        print("whylog add: no command given (usage: whylog add -m WHY CMD)", file=sys.stderr)
        return 2
    entry = append_entry(args.file, cmd=cmd, why=args.message, cwd=os.getcwd(), exit=args.exit)
    print(f"recorded #{entry.id}")
    return 0


def short_path(path: str) -> str:
    home = str(Path.home())
    if path == home or path.startswith(home + os.sep):
        return "~" + path[len(home):]
    return path


def format_status(entry: Entry) -> str:
    if entry.exit is None:
        return "added"
    status = "ok" if entry.exit == 0 else f"exit {entry.exit}"
    if entry.duration is not None:
        status += f", {entry.duration:.1f}s"
    return status


def format_entry(entry: Entry) -> str:
    when = entry.when.astimezone().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"#{entry.id}  {when}  {format_status(entry)}  {short_path(entry.cwd)}",
        f"    $ {entry.cmd}",
    ]
    if entry.why:
        lines.append(f"    why: {entry.why}")
    return "\n".join(lines)


def selected_entries(args: argparse.Namespace) -> list[Entry] | None:
    """Read the journal and apply the shared filter options. None on bad input."""
    try:
        since = parse_since(args.since) if args.since else None
    except ValueError as err:
        print(f"whylog: {err}", file=sys.stderr)
        return None
    return filter_entries(
        read_entries(args.file),
        grep=args.grep,
        here=Path.cwd() if args.here else None,
        since=since,
        failed=args.failed,
        last=args.last,
    )


def cmd_list(args: argparse.Namespace) -> int:
    entries = selected_entries(args)
    if entries is None:
        return 2
    if entries:
        print("\n\n".join(format_entry(e) for e in entries))
    return 0


def add_filter_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-g", "--grep", metavar="TEXT", help="match TEXT in the command or reason")
    parser.add_argument("--here", action="store_true", help="only commands run in this folder or below")
    parser.add_argument("--since", metavar="WHEN", help="30m, 12h, 7d, 2w or a date like 2026-10-01")
    parser.add_argument("--failed", action="store_true", help="only commands that exited non-zero")
    parser.add_argument("-n", "--last", type=int, metavar="N", help="only the newest N matches")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="whylog",
        description="A command journal that records what you ran and why.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--file",
        type=Path,
        default=None,
        help="journal file (default: $WHYLOG_FILE or $XDG_DATA_HOME/why-log/journal.jsonl)",
    )
    sub = parser.add_subparsers(dest="action", required=True)

    run = sub.add_parser("run", help="run a command and record it")
    run.add_argument("-m", "--message", default="", help="why you are running it")
    run.add_argument("command", nargs=argparse.REMAINDER, help="the command, after --")
    run.set_defaults(func=cmd_run)

    add = sub.add_parser("add", help="record a command you already ran, without running it")
    add.add_argument("-m", "--message", default="", help="why you ran it")
    add.add_argument("--exit", type=int, default=None, help="exit code, if you know it")
    add.add_argument("command", nargs=argparse.REMAINDER, help='the command, best quoted: "tar xzf a.tgz"')
    add.set_defaults(func=cmd_add)

    ls = sub.add_parser("list", aliases=["ls"], help="show recorded commands, oldest first")
    add_filter_options(ls)
    ls.set_defaults(func=cmd_list)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.file is None:
        args.file = default_path()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
