# pygit

A minimal Git-like command-line utility written in Python.

`pygit` is an educational implementation of core Git mechanics:
- object hashing and storage
- binary index read/write
- tree writing
- commit object creation
- working tree inspection

It is intentionally small and focused on learning internals rather than replacing Git.

## Requirements

- Python `>=3.10`
- `uv` package manager

## Project Layout

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

## Setup

Install dependencies and create the environment:

```bash
uv sync
```

Run the CLI:

```bash
uv run pygit --help
```

You can also run it as a module:

```bash
uv run python -m src
```

## Commands

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
```

## Quick Start

```bash
# create a repository
mkdir demo && cd demo
uv run pygit init .

# add content
echo "hello" > hello.txt
uv run pygit add hello.txt

# inspect staged entries
uv run pygit ls-files -s

# create a commit
uv run pygit commit -m "first commit"

# check status
uv run pygit status
```

## Notes

- `pygit` currently operates on the `master` branch reference.
- Author info is read from `GIT_AUTHOR_NAME` / `GIT_AUTHOR_EMAIL` (or committer variants).  
  Defaults are used if env vars are not set.
- Remote operations (`push`, fetch/pull workflows) are not implemented yet.

## Development

Run formatting/linting/tests using your preferred tools via `uv`.

Examples:

```bash
uv run python -m compileall -q src
```

When adding a package, use:

```bash
uv add <package>
```

## Roadmap Ideas

- `log` command for commit history
- `rm` and unstage support
- ignore patterns (`.gitignore` awareness in add/status)
- lightweight branch and checkout support
- remote push support
