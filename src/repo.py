from __future__ import annotations

from pathlib import Path


class RepositoryNotFoundError(RuntimeError):
    """Raised when no .git directory can be discovered."""


def find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").is_dir():
            return candidate
    raise RepositoryNotFoundError("could not find .git directory from current path")


def git_dir(repo_root: Path) -> Path:
    return repo_root / ".git"


def ensure_repo(start: Path | None = None) -> Path:
    return find_repo_root(start=start)

