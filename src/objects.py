from __future__ import annotations

import hashlib
import zlib
from dataclasses import dataclass
from pathlib import Path

from repo import git_dir


VALID_OBJECT_TYPES = {"blob", "tree", "commit"}


@dataclass(frozen=True)
class GitObject:
    obj_type: str
    data: bytes
    sha1: str


def _object_path(repo_root: Path, sha1: str) -> Path:
    return git_dir(repo_root) / "objects" / sha1[:2] / sha1[2:]


def hash_object(data: bytes, obj_type: str, repo_root: Path, write: bool = True) -> str:
    if obj_type not in VALID_OBJECT_TYPES:
        raise ValueError(f"unsupported object type: {obj_type}")
    header = f"{obj_type} {len(data)}".encode()
    full_data = header + b"\x00" + data
    sha1 = hashlib.sha1(full_data).hexdigest()
    if write:
        path = _object_path(repo_root, sha1)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(zlib.compress(full_data))
    return sha1


def resolve_object(repo_root: Path, prefix: str) -> str:
    if len(prefix) < 4:
        raise ValueError("object id prefix must have at least 4 hex chars")
    if len(prefix) == 40:
        path = _object_path(repo_root, prefix)
        if path.is_file():
            return prefix
        raise FileNotFoundError(f"object {prefix} not found")
    objects_dir = git_dir(repo_root) / "objects"
    directory = objects_dir / prefix[:2]
    if not directory.is_dir():
        raise FileNotFoundError(f"object {prefix} not found")
    matches = [f"{prefix[:2]}{p.name}" for p in directory.iterdir() if p.name.startswith(prefix[2:])]
    if not matches:
        raise FileNotFoundError(f"object {prefix} not found")
    if len(matches) > 1:
        raise ValueError(f"object prefix {prefix} is ambiguous")
    return matches[0]


def read_object(repo_root: Path, object_id: str) -> GitObject:
    sha1 = resolve_object(repo_root, object_id)
    path = _object_path(repo_root, sha1)
    compressed = path.read_bytes()
    full_data = zlib.decompress(compressed)
    header, data = full_data.split(b"\x00", 1)
    obj_type_bytes, size_bytes = header.split(b" ", 1)
    obj_type = obj_type_bytes.decode()
    expected_size = int(size_bytes.decode())
    if len(data) != expected_size:
        raise ValueError(f"malformed object {sha1}: expected size {expected_size}, got {len(data)}")
    return GitObject(obj_type=obj_type, data=data, sha1=sha1)
