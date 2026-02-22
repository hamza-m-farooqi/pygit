from __future__ import annotations

import hashlib
import os
import stat
import struct
from dataclasses import dataclass
from pathlib import Path

from objects import hash_object
from repo import git_dir

INDEX_SIGNATURE = b"DIRC"
INDEX_VERSION = 2
INDEX_HEADER = struct.Struct("!4sLL")
INDEX_ENTRY_HEAD = struct.Struct("!LLLLLLLLLL20sH")


@dataclass(frozen=True)
class IndexEntry:
    ctime_s: int
    ctime_n: int
    mtime_s: int
    mtime_n: int
    dev: int
    ino: int
    mode: int
    uid: int
    gid: int
    size: int
    sha1: bytes
    flags: int
    path: str


def _index_path(repo_root: Path) -> Path:
    return git_dir(repo_root) / "index"


def read_index(repo_root: Path) -> list[IndexEntry]:
    path = _index_path(repo_root)
    if not path.exists():
        return []
    data = path.read_bytes()
    if len(data) < 32:
        raise ValueError("index file is too short")
    digest = hashlib.sha1(data[:-20]).digest()
    if digest != data[-20:]:
        raise ValueError("invalid index checksum")
    signature, version, num_entries = INDEX_HEADER.unpack(data[:12])
    if signature != INDEX_SIGNATURE:
        raise ValueError("invalid index signature")
    if version != INDEX_VERSION:
        raise ValueError(f"unsupported index version {version}")

    entries: list[IndexEntry] = []
    body = data[12:-20]
    i = 0
    while i + INDEX_ENTRY_HEAD.size <= len(body) and len(entries) < num_entries:
        fields_end = i + INDEX_ENTRY_HEAD.size
        fields = INDEX_ENTRY_HEAD.unpack(body[i:fields_end])
        path_end = body.find(b"\x00", fields_end)
        if path_end == -1:
            raise ValueError("unterminated index path entry")
        raw_path = body[fields_end:path_end]
        entry = IndexEntry(*fields, raw_path.decode())
        entries.append(entry)
        entry_len = ((INDEX_ENTRY_HEAD.size + len(raw_path) + 8) // 8) * 8
        i += entry_len
    if len(entries) != num_entries:
        raise ValueError("invalid number of index entries")
    return entries


def write_index(repo_root: Path, entries: list[IndexEntry]) -> None:
    payload = bytearray()
    payload.extend(INDEX_HEADER.pack(INDEX_SIGNATURE, INDEX_VERSION, len(entries)))
    for entry in sorted(entries, key=lambda item: item.path):
        encoded_path = entry.path.encode()
        payload.extend(
            INDEX_ENTRY_HEAD.pack(
                entry.ctime_s,
                entry.ctime_n,
                entry.mtime_s,
                entry.mtime_n,
                entry.dev,
                entry.ino,
                entry.mode,
                entry.uid,
                entry.gid,
                entry.size,
                entry.sha1,
                entry.flags,
            )
        )
        payload.extend(encoded_path)
        payload.append(0)
        while len(payload) % 8 != 0:
            payload.append(0)
    payload.extend(hashlib.sha1(payload).digest())
    _index_path(repo_root).write_bytes(payload)


def build_entry(repo_root: Path, file_path: Path) -> IndexEntry:
    st = file_path.stat()
    rel_path = file_path.relative_to(repo_root).as_posix()
    sha1_hex = hash_object(file_path.read_bytes(), "blob", repo_root=repo_root, write=True)
    executable = bool(stat.S_IMODE(st.st_mode) & stat.S_IXUSR)
    mode = 0o100755 if executable else 0o100644
    flags = min(len(rel_path.encode()), 0xFFF)
    return IndexEntry(
        ctime_s=int(st.st_ctime),
        ctime_n=getattr(st, "st_ctime_ns", int(st.st_ctime * 1_000_000_000)) % 1_000_000_000,
        mtime_s=int(st.st_mtime),
        mtime_n=getattr(st, "st_mtime_ns", int(st.st_mtime * 1_000_000_000)) % 1_000_000_000,
        dev=st.st_dev,
        ino=st.st_ino,
        mode=mode,
        uid=st.st_uid,
        gid=st.st_gid,
        size=st.st_size,
        sha1=bytes.fromhex(sha1_hex),
        flags=flags,
        path=rel_path,
    )


def is_ignored_path(path: Path) -> bool:
    return ".git" in path.parts


def list_working_tree_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(repo_root):
        root = Path(dirpath)
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for filename in filenames:
            absolute = root / filename
            if is_ignored_path(absolute.relative_to(repo_root)):
                continue
            files.append(absolute)
    return sorted(files)
