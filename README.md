# why-log

A command journal for the terminal. It records the commands you run together with
*why* you ran them, the directory, the exit code and how long they took, so you can
find that one-off fix again weeks later.

It is for people who live in a shell and keep forgetting what a past command was for.
Shell history keeps the command; why-log keeps the reason.

Built with Python 3.11+ and the standard library only. Tests use pytest.

Status: work in progress toward v0.1. See [ROADMAP.md](ROADMAP.md).

## Install

```bash
git clone https://github.com/landry-some/why-log.git
cd why-log
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
```

This puts a `whylog` command in the virtual environment.

## Test

```bash
pytest
```

## License

MIT, see [LICENSE](LICENSE).
