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
- [x] `branch`
- [x] `checkout`
- [x] `rm`
- [x] `restore --staged`
- [x] `.gitignore`-aware `add/status`
- [x] improved `.gitignore` compatibility (Git-style wildmatch)
- [x] `commit --amend`
- [x] `reset --soft|--mixed`
- [x] `remote` (add/list/get-url/remove)
- [x] `push`

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

## Install As Package (After Cloning)

```bash
git clone <your-fork-or-repo-url>
cd pygit
```

Install as a user-level CLI command with `uv`:

```bash
uv tool install --from . pygit
```

Then run from anywhere:

```bash
pygit --help
```

If you update local code and want to reinstall:

```bash
uv tool install --from . pygit --force
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
pygit commit --amend [-m "<message>"]
pygit reset [--soft|--mixed] <revision>
pygit remote
pygit remote list [-v]
pygit remote add <name> <url>
pygit remote get-url <name>
pygit remote remove <name>
pygit push [<remote>] [<branch>]
pygit log [--oneline] [-n <count>]
pygit rev-parse <revision>
pygit branch [<name>]
pygit checkout <branch-or-revision>
pygit rm <path> [<path> ...]
pygit restore --staged <path> [<path> ...]
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

Add runtime dependencies with:

```bash
uv add <package>
```

Add development dependencies with:

```bash
uv add --dev <package>
```

Basic sanity check:

```bash
uv run python -m compileall -q src
```

Run tests:

```bash
uv sync --extra dev
uv run pytest
```

## Notes

- `pygit branch` lists local branches and can create a new branch at current `HEAD`.
- `pygit checkout` switches to a branch or detaches `HEAD` at a revision.
- `pygit rm` removes tracked files from both index and working tree.
- `pygit restore --staged` resets staged content for paths to match `HEAD`.
- `status` and `add` respect root `.gitignore` patterns with Git-style wildmatch behavior.
- Author values come from `GIT_AUTHOR_NAME` / `GIT_AUTHOR_EMAIL` (or committer variants).
- If env vars are missing, default author values are used.

## Roadmap

- commit history (`log`)
- remote push support

## License

Add your preferred license (MIT/Apache-2.0/etc.) in a `LICENSE` file.
