from __future__ import annotations

from pathlib import Path

from objects import resolve_object
from repo import git_dir


def _read_ref_file(path: Path) -> str | None:
    if not path.exists():
        return None
    value = path.read_text(encoding="utf-8").strip()
    return value or None


def head_ref(repo_root: Path) -> str | None:
    head_path = git_dir(repo_root) / "HEAD"
    head_value = _read_ref_file(head_path)
    if not head_value:
        return None
    if head_value.startswith("ref: "):
        return head_value[5:].strip()
    return None


def head_commit(repo_root: Path) -> str | None:
    ref = head_ref(repo_root)
    if ref:
        return _read_ref_file(git_dir(repo_root) / ref)
    head_path = git_dir(repo_root) / "HEAD"
    value = _read_ref_file(head_path)
    return value


def current_branch(repo_root: Path) -> str | None:
    ref = head_ref(repo_root)
    if not ref:
        return None
    prefix = "refs/heads/"
    if ref.startswith(prefix):
        return ref[len(prefix) :]
    return ref


def list_branches(repo_root: Path) -> list[str]:
    heads = git_dir(repo_root) / "refs" / "heads"
    if not heads.exists():
        return []
    return sorted(p.name for p in heads.iterdir() if p.is_file())


def resolve_head(repo_root: Path) -> str:
    commit_id = head_commit(repo_root)
    if not commit_id:
        raise ValueError("HEAD does not point to a commit")
    return commit_id


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
