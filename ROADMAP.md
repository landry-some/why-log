# Roadmap

Planned work after v0.1, with rough estimates. Total: about 32 hours.

## v0.1 (first weekend)

- [x] `whylog run -m "why" -- <cmd...>`: run a command and record it
- [x] `whylog add -m "why" "<cmd>"`: record a command without running it
- [x] `whylog list` with `--grep`, `--here`, `--since`, `--failed`, `-n`
- [x] `whylog export`: print entries as Markdown

## Features (15 h)

- [ ] Shell hook for bash and zsh that asks "why?" after slow or failed commands (5 h)
- [ ] `whylog rerun <id>`: run a recorded command again in its original directory (2 h)
- [ ] Tags: `-t deploy` on `run`/`add`, `--tag` filter on `list`/`export` (2 h)
- [ ] `whylog edit <id>` to change the reason, `whylog rm <id>` to drop an entry (2 h)
- [ ] Optional `--keep-output N` to store the last N lines of output (3 h)
- [ ] `whylog export --json` for scripting (1 h)

## Bugs and edge cases (6 h)

- [ ] Lock the journal file so two shells writing at once can't interleave lines (1.5 h)
- [x] Skip and report corrupt journal lines instead of failing (1 h)
- [ ] Forward Ctrl-C / SIGTERM to the child and record the signal exit (1.5 h)
- [ ] Show times in local time correctly across DST changes (1 h)
- [ ] Handle arguments and paths that are not valid UTF-8 (1 h)

## Refactors (5 h)

- [ ] Move journal reads/writes behind a small storage interface (2 h)
- [ ] Optional SQLite backend for large journals, with a migration command (3 h)

## Tests (3.5 h)

- [ ] End-to-end tests that call the installed `whylog` command (2 h)
- [ ] CI on Linux and macOS with GitHub Actions (1.5 h)

## Docs (2.5 h)

- [ ] Man page (1.5 h)
- [ ] Recipes: shell aliases, journaling a deploy, sharing an export (1 h)
