from __future__ import annotations

import argparse
import difflib
import os
import time
from pathlib import Path

from index import IndexEntry, build_entry, list_working_tree_files, read_index, write_index
from objects import hash_object, read_object
from repo import ensure_repo, git_dir
from revisions import current_branch, head_commit, list_branches, resolve_revision


def cmd_init(args: argparse.Namespace) -> int:
    repo_path = Path(args.path).resolve()
    git_path = repo_path / ".git"
    git_path.mkdir(parents=True, exist_ok=False)
    (git_path / "objects").mkdir()
    (git_path / "refs" / "heads").mkdir(parents=True)
    (git_path / "HEAD").write_text("ref: refs/heads/master\n", encoding="utf-8")
    print(f"initialized empty repository: {repo_path}")
    return 0


def cmd_hash_object(args: argparse.Namespace) -> int:
    repo_root = ensure_repo()
    data = Path(args.path).read_bytes()
    sha1 = hash_object(data, obj_type=args.type, repo_root=repo_root, write=args.write)
    print(sha1)
    return 0


def _parse_tree(data: bytes) -> list[tuple[str, str, str]]:
    i = 0
    entries: list[tuple[str, str, str]] = []
    while i < len(data):
        mode_end = data.index(b" ", i)
        mode = data[i:mode_end].decode()
        name_end = data.index(b"\x00", mode_end)
        name = data[mode_end + 1 : name_end].decode()
        sha1_bytes = data[name_end + 1 : name_end + 21]
        entries.append((mode, sha1_bytes.hex(), name))
        i = name_end + 21
    return entries


def cmd_cat_file(args: argparse.Namespace) -> int:
    repo_root = ensure_repo()
    obj = read_object(repo_root, resolve_revision(repo_root, args.object))
    if args.type_only:
        print(obj.obj_type)
        return 0
    if args.size_only:
        print(len(obj.data))
        return 0
    if obj.obj_type == "blob":
        print(obj.data.decode(errors="replace"), end="")
        return 0
    if obj.obj_type == "commit":
        print(obj.data.decode(errors="replace"), end="")
        return 0
    if obj.obj_type == "tree":
        for mode, sha1, name in _parse_tree(obj.data):
            nested = read_object(repo_root, sha1)
            print(f"{mode:>6} {nested.obj_type:>6} {sha1}    {name}")
        return 0
    raise ValueError(f"unsupported object type {obj.obj_type}")


def _resolve_paths(repo_root: Path, raw_paths: list[str]) -> list[Path]:
    resolved: list[Path] = []
    for raw in raw_paths:
        candidate = (Path.cwd() / raw).resolve()
        if not candidate.exists():
            raise FileNotFoundError(f"path not found: {raw}")
        candidate.relative_to(repo_root)
        if candidate.is_dir():
            for root, dirnames, filenames in os.walk(candidate):
                root_path = Path(root)
                dirnames[:] = [d for d in dirnames if d != ".git"]
                for filename in filenames:
                    file_path = root_path / filename
                    rel = file_path.relative_to(repo_root)
                    if ".git" in rel.parts:
                        continue
                    resolved.append(file_path)
        else:
            if ".git" in candidate.relative_to(repo_root).parts:
                continue
            resolved.append(candidate)
    unique = sorted(set(resolved))
    for path in unique:
        path.relative_to(repo_root)
    return unique


def cmd_add(args: argparse.Namespace) -> int:
    repo_root = ensure_repo()
    entries = read_index(repo_root)
    by_path = {entry.path: entry for entry in entries}
    for file_path in _resolve_paths(repo_root, args.paths):
        if file_path.is_file():
            entry = build_entry(repo_root, file_path)
            by_path[entry.path] = entry
    write_index(repo_root, list(by_path.values()))
    return 0


def cmd_ls_files(args: argparse.Namespace) -> int:
    repo_root = ensure_repo()
    for entry in read_index(repo_root):
        if args.stage:
            print(f"{entry.mode:o} {entry.sha1.hex()} 0\t{entry.path}")
        else:
            print(entry.path)
    return 0


def _status_sets(repo_root: Path) -> tuple[list[str], list[str], list[str], list[str]]:
    entries = read_index(repo_root)
    staged_paths = {entry.path for entry in entries}
    entries_by_path = {entry.path: entry for entry in entries}
    head_entries = _head_index_like_entries(repo_root)
    working_files = list_working_tree_files(repo_root)
    working_paths = {path.relative_to(repo_root).as_posix() for path in working_files}

    changed = sorted(
        p
        for p in (staged_paths & working_paths)
        if hash_object((repo_root / p).read_bytes(), "blob", repo_root=repo_root, write=False)
        != entries_by_path[p].sha1.hex()
    )
    deleted = sorted(staged_paths - working_paths)
    untracked = sorted(working_paths - staged_paths)
    staged = sorted(
        path
        for path in staged_paths
        if head_entries.get(path) != entries_by_path[path].sha1.hex()
    )
    return staged, changed, deleted, untracked


def cmd_status(args: argparse.Namespace) -> int:
    repo_root = ensure_repo()
    staged, changed, deleted, untracked = _status_sets(repo_root)
    branch = current_branch(repo_root)
    if branch:
        print(f"On branch {branch}")
    else:
        detached_at = (_current_head_commit(repo_root) or "unknown")[:7]
        print(f"HEAD detached at {detached_at}")
    print("")
    if staged:
        print("Changes to be committed:")
        for path in staged:
            print(f"  staged:   {path}")
        print("")
    if changed or deleted:
        print("Changes not staged for commit:")
        for path in changed:
            print(f"  modified: {path}")
        for path in deleted:
            print(f"  deleted:  {path}")
        print("")
    if untracked:
        print("Untracked files:")
        for path in untracked:
            print(f"  {path}")
        print("")
    if not any([staged, changed, deleted, untracked]):
        print("nothing to commit, working tree clean")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    repo_root = ensure_repo()
    entries = read_index(repo_root)
    entries_by_path = {entry.path: entry for entry in entries}
    working_paths = {path.relative_to(repo_root).as_posix() for path in list_working_tree_files(repo_root)}
    changed_paths = sorted(
        p
        for p in (set(entries_by_path) & working_paths)
        if hash_object((repo_root / p).read_bytes(), "blob", repo_root=repo_root, write=False)
        != entries_by_path[p].sha1.hex()
    )
    for rel in changed_paths:
        index_blob = read_object(repo_root, entries_by_path[rel].sha1.hex()).data.decode(errors="replace").splitlines()
        working_blob = (repo_root / rel).read_text(encoding="utf-8", errors="replace").splitlines()
        diff = difflib.unified_diff(index_blob, working_blob, fromfile=f"a/{rel}", tofile=f"b/{rel}", lineterm="")
        print("\n".join(diff))
    return 0


def _write_tree_recursive(repo_root: Path, children: dict[str, object]) -> str:
    records: list[bytes] = []
    for name in sorted(children):
        node = children[name]
        if isinstance(node, IndexEntry):
            mode = f"{node.mode:o}".encode()
            record = mode + b" " + name.encode() + b"\x00" + node.sha1
            records.append(record)
            continue
        sha1 = _write_tree_recursive(repo_root, node)
        record = b"40000 " + name.encode() + b"\x00" + bytes.fromhex(sha1)
        records.append(record)
    return hash_object(b"".join(records), obj_type="tree", repo_root=repo_root, write=True)


def cmd_write_tree(args: argparse.Namespace) -> int:
    repo_root = ensure_repo()
    entries = read_index(repo_root)
    tree: dict[str, object] = {}
    for entry in entries:
        parts = entry.path.split("/")
        cursor = tree
        for part in parts[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[parts[-1]] = entry
    sha1 = _write_tree_recursive(repo_root, tree)
    print(sha1)
    return 0


def _current_head_commit(repo_root: Path) -> str | None:
    return head_commit(repo_root)


def _head_index_like_entries(repo_root: Path) -> dict[str, str]:
    commit_id = _current_head_commit(repo_root)
    if not commit_id:
        return {}
    commit_obj = read_object(repo_root, commit_id)
    tree_sha = None
    for line in commit_obj.data.decode(errors="replace").splitlines():
        if line.startswith("tree "):
            tree_sha = line.split(" ", 1)[1].strip()
            break
    if not tree_sha:
        return {}
    return _flatten_tree(repo_root, tree_sha)


def _flatten_tree(repo_root: Path, tree_sha: str, prefix: str = "") -> dict[str, str]:
    flat: dict[str, str] = {}
    tree = read_object(repo_root, tree_sha)
    for mode, sha, name in _parse_tree(tree.data):
        path = f"{prefix}{name}" if not prefix else f"{prefix}/{name}"
        nested = read_object(repo_root, sha)
        if nested.obj_type == "tree":
            flat.update(_flatten_tree(repo_root, sha, path))
        else:
            flat[path] = sha
    return flat


def _current_author() -> str:
    name = os.getenv("GIT_AUTHOR_NAME") or os.getenv("GIT_COMMITTER_NAME")
    email = os.getenv("GIT_AUTHOR_EMAIL") or os.getenv("GIT_COMMITTER_EMAIL")
    if not name:
        name = "pygit-user"
    if not email:
        email = "pygit@example.com"
    return f"{name} <{email}>"


def cmd_commit(args: argparse.Namespace) -> int:
    repo_root = ensure_repo()
    entries = read_index(repo_root)
    if not entries:
        raise ValueError("cannot commit: index is empty")

    tree_sha1 = _write_tree_recursive(repo_root, _index_to_tree_map(entries))
    parent = _current_head_commit(repo_root)

    timestamp = int(time.time())
    utc_offset = -time.timezone
    sign = "+" if utc_offset >= 0 else "-"
    offset_hours = abs(utc_offset) // 3600
    offset_minutes = (abs(utc_offset) // 60) % 60
    author_time = f"{timestamp} {sign}{offset_hours:02}{offset_minutes:02}"
    author = _current_author()

    lines = [f"tree {tree_sha1}"]
    if parent:
        lines.append(f"parent {parent}")
    lines.append(f"author {author} {author_time}")
    lines.append(f"committer {author} {author_time}")
    lines.append("")
    lines.append(args.message)
    lines.append("")
    commit_data = "\n".join(lines).encode()
    commit_sha1 = hash_object(commit_data, obj_type="commit", repo_root=repo_root, write=True)
    master = git_dir(repo_root) / "refs" / "heads" / "master"
    master.parent.mkdir(parents=True, exist_ok=True)
    master.write_text(f"{commit_sha1}\n", encoding="utf-8")
    print(f"committed to master: {commit_sha1}")
    return 0


def _parse_commit_payload(data: bytes) -> tuple[dict[str, str], str]:
    text = data.decode(errors="replace")
    header_text, _, message = text.partition("\n\n")
    headers: dict[str, str] = {}
    for line in header_text.splitlines():
        if " " not in line:
            continue
        key, value = line.split(" ", 1)
        headers[key] = value
    return headers, message.rstrip("\n")


def cmd_log(args: argparse.Namespace) -> int:
    repo_root = ensure_repo()
    try:
        commit_id = resolve_revision(repo_root, "HEAD")
    except ValueError:
        print("fatal: your current branch does not have any commits yet")
        return 1

    max_count = args.max_count
    printed = 0
    while commit_id and printed < max_count:
        obj = read_object(repo_root, commit_id)
        if obj.obj_type != "commit":
            raise ValueError(f"object {commit_id} is not a commit")

        headers, message = _parse_commit_payload(obj.data)
        summary = message.splitlines()[0] if message else ""
        if args.oneline:
            print(f"{commit_id[:7]} {summary}")
        else:
            print(f"commit {commit_id}")
            author = headers.get("author")
            if author:
                print(f"Author: {author}")
            print("")
            if summary:
                print(f"    {summary}")
            print("")
        commit_id = headers.get("parent")
        printed += 1
    return 0


def cmd_rev_parse(args: argparse.Namespace) -> int:
    repo_root = ensure_repo()
    print(resolve_revision(repo_root, args.revision))
    return 0


def cmd_branch(args: argparse.Namespace) -> int:
    repo_root = ensure_repo()
    if args.name is None:
        active = current_branch(repo_root)
        for branch in list_branches(repo_root):
            marker = "*" if branch == active else " "
            print(f"{marker} {branch}")
        return 0

    commit_id = _current_head_commit(repo_root)
    if not commit_id:
        raise ValueError("cannot create branch: HEAD does not point to a commit")
    target = git_dir(repo_root) / "refs" / "heads" / args.name
    if target.exists():
        raise ValueError(f"branch '{args.name}' already exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"{commit_id}\n", encoding="utf-8")
    print(f"branch '{args.name}' created at {commit_id[:7]}")
    return 0


def _index_to_tree_map(entries: list[IndexEntry]) -> dict[str, object]:
    tree: dict[str, object] = {}
    for entry in entries:
        parts = entry.path.split("/")
        cursor = tree
        for part in parts[:-1]:
            next_node = cursor.get(part)
            if not isinstance(next_node, dict):
                next_node = {}
                cursor[part] = next_node
            cursor = next_node
        cursor[parts[-1]] = entry
    return tree
