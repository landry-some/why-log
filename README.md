# why-log

A command journal for the terminal. It records the commands you run together with
*why* you ran them, the directory, the exit code and how long they took, so you can
find that one-off fix again weeks later.

It is for people who live in a shell and keep forgetting what a past command was for.
Shell history keeps the command; why-log keeps the reason.

Built with Python 3.11+ and the standard library only. Tests use pytest.

## Install

```bash
git clone https://github.com/landry-some/why-log.git
cd why-log
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
```

This puts a `whylog` command in the virtual environment.

## Try it on the sample journal

`examples/journal.jsonl` is a made-up journal. Point `--file` at it:

```bash
whylog --file examples/journal.jsonl list
whylog --file examples/journal.jsonl list --failed
whylog --file examples/journal.jsonl export --grep deploy --title "Blog deploys"
```

## Usage

### Run and record a command

```bash
whylog run -m "shrink the video for the upload limit" -- ffmpeg -i in.mov -crf 28 out.mp4
```

The command runs in your terminal as usual (its input and output are not captured).
When it ends, why-log appends an entry with the time, the current folder, the
command, your reason, the exit code and the duration. `whylog run` exits with the
command's own exit code, so it works in scripts and `&&` chains.

Put the command after `--`. A command that can't be found is recorded with exit
code 127. A command stopped by a signal is recorded as 128 + the signal number
(Ctrl-C gives 130), like the shell does.

### Record a command you already ran

```bash
whylog add -m "disk was at 97%" "docker system prune -a --volumes"
whylog add --exit 1 -m "flaky on CI too" -- pytest -x
```

`add` does not run anything. The entry has no exit code unless you pass `--exit`.

### Tag entries

```bash
whylog run -t deploy -t blog -m "publish the backups post" -- make deploy
whylog add -t cleanup -m "disk was at 97%" "docker system prune -a"
```

`-t` / `--tag` works on `run` and `add` and can be repeated. Tags show in brackets
after the folder in `list` and after the status in `export`.

### List entries

```bash
whylog list                    # everything, oldest first (alias: whylog ls)
whylog list -n 5               # the newest 5
whylog list --grep docker      # text in the command or the reason, any case
whylog list --here             # run in this folder or a folder below it
whylog list --since 7d         # 30m, 12h, 7d, 2w, or a date like 2026-10-01
whylog list --failed           # commands that exited non-zero
whylog list --tag deploy       # entries tagged exactly "deploy"
```

Filters combine. Output looks like this:

```
#2  2026-10-20 09:15  exit 2, 6.8s  /home/demo/code/blog
    $ make deploy
    why: publish the post about home lab backups
```

Times are shown in your local time zone.

### Export as Markdown

```bash
whylog export --since 2w --title "Last two weeks" -o notes.md
```

`export` takes the same filters as `list` and writes Markdown grouped by day, with
each command in a code block, ready to paste into notes or a runbook. Without `-o`
it prints to stdout.

## Where the journal lives

By default the journal is `$XDG_DATA_HOME/why-log/journal.jsonl`, which is
`~/.local/share/why-log/journal.jsonl` on most Linux systems. Set `WHYLOG_FILE`
to use another file, or pass `--file PATH` before the subcommand.

The file is JSON Lines, one entry per line:

```json
{"id": 3, "time": "2026-10-20T09:18:02+00:00", "cwd": "/home/demo/code/blog", "cmd": "make deploy", "why": "retry after fixing the broken image link", "exit": 0, "duration": 7.302, "tags": ["deploy"]}
```

`exit` and `duration` are `null` for entries made with `add`. `tags` may be missing
in older entries; it then counts as no tags. The file is plain text,
so you can edit it by hand or keep it in your dotfiles. A line that isn't a valid
entry (say, after a bad hand edit) is skipped with a warning naming its line number,
and the rest of the journal still loads.

## Test

```bash
pytest
```

## Plans

See [ROADMAP.md](ROADMAP.md): shell hooks that ask "why?" after slow or failed
commands, `rerun`, editing entries, file locking and more.

## License

MIT, see [LICENSE](LICENSE).
