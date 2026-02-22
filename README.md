# pygit

Minimal Git-like CLI written in Python for learning how Git works under the hood.

## Why this project

`pygit` focuses on core plumbing concepts:
- Git object hashing and storage
- binary index parsing/writing
- tree object generation
- commit object creation
- working tree status and diff

This is an educational tool, not a replacement for `git`.

## Features

- [x] `init`
- [x] `hash-object`
- [x] `cat-file`
- [x] `add`
- [x] `ls-files`
- [x] `status`
- [x] `diff`
- [x] `write-tree`
- [x] `commit`
- [x] `log`
- [x] `rev-parse`
- [ ] `push`

## Requirements

- Python `>=3.10`
- [`uv`](https://docs.astral.sh/uv/)

## Installation / Setup

```bash
uv sync
```

Run CLI help:

```bash
uv run pygit --help
```

## Quick Start

```bash
mkdir demo && cd demo
uv run pygit init .

echo "hello pygit" > hello.txt
uv run pygit add hello.txt
uv run pygit commit -m "first commit"
uv run pygit status
```

## Command Reference

```bash
pygit init <path>
pygit hash-object [-w] [-t blob|tree|commit] <file>
pygit cat-file (-p|-t|-s) <object-id-or-prefix>
pygit add <path> [<path> ...]
pygit ls-files [-s]
pygit status
pygit diff
pygit write-tree
pygit commit -m "<message>"
pygit log [--oneline] [-n <count>]
pygit rev-parse <revision>
```

## Development

Project layout:

```text
.
├── pyproject.toml
├── uv.lock
└── src/
    ├── cli.py
    ├── commands.py
    ├── index.py
    ├── objects.py
    ├── repo.py
    └── __main__.py
```

Add dependencies with:

```bash
uv add <package>
```

Basic sanity check:

```bash
uv run python -m compileall -q src
```

## Notes

- Branch reference is currently `master`.
- Author values come from `GIT_AUTHOR_NAME` / `GIT_AUTHOR_EMAIL` (or committer variants).
- If env vars are missing, default author values are used.

## Roadmap

- commit history (`log`)
- unstage/remove support
- `.gitignore`-aware staging/status
- branch and checkout basics
- remote push support

## License

Add your preferred license (MIT/Apache-2.0/etc.) in a `LICENSE` file.
