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
from .journal import append_entry, default_path


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


def cmd_run(args: argparse.Namespace) -> int:
    argv = args.command
    if argv and argv[0] == "--":
        argv = argv[1:]
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

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.file is None:
        args.file = default_path()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
