from __future__ import annotations

from pathlib import Path

from objects import resolve_object
from repo import git_dir


def _read_ref_file(path: Path) -> str | None:
    if not path.exists():
        return None
    value = path.read_text(encoding="utf-8").strip()
    return value or None


def resolve_head(repo_root: Path) -> str:
    head_path = git_dir(repo_root) / "HEAD"
    head_value = _read_ref_file(head_path)
    if not head_value:
        raise ValueError("HEAD is missing")
    if head_value.startswith("ref: "):
        ref = head_value[5:].strip()
        commit_id = _read_ref_file(git_dir(repo_root) / ref)
        if not commit_id:
            raise ValueError(f"reference {ref} does not point to a commit")
        return commit_id
    return head_value


def resolve_revision(repo_root: Path, rev: str) -> str:
    if rev == "HEAD":
        return resolve_head(repo_root)
    if rev.startswith("refs/"):
        value = _read_ref_file(git_dir(repo_root) / rev)
        if value:
            return value
    branch_value = _read_ref_file(git_dir(repo_root) / "refs" / "heads" / rev)
    if branch_value:
        return branch_value
    return resolve_object(repo_root, rev)

