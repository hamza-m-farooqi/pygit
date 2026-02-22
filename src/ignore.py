from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import PurePosixPath


@dataclass(frozen=True)
class IgnoreRule:
    pattern: str
    negated: bool
    directory_only: bool
    anchored: bool
    has_slash: bool


def load_ignore_rules(repo_root) -> list[IgnoreRule]:
    ignore_file = repo_root / ".gitignore"
    if not ignore_file.exists():
        return []
    rules: list[IgnoreRule] = []
    for line in ignore_file.read_text(encoding="utf-8", errors="replace").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        negated = raw.startswith("!")
        if negated:
            raw = raw[1:]
            if not raw:
                continue
        anchored = raw.startswith("/")
        if anchored:
            raw = raw[1:]
        directory_only = raw.endswith("/")
        if directory_only:
            raw = raw.rstrip("/")
        has_slash = "/" in raw
        rules.append(
            IgnoreRule(
                pattern=raw,
                negated=negated,
                directory_only=directory_only,
                anchored=anchored,
                has_slash=has_slash,
            )
        )
    return rules


def _rule_matches(rule: IgnoreRule, rel_path: str, is_dir: bool) -> bool:
    rel_path = rel_path.strip("/")
    if not rel_path:
        return False
    if rule.directory_only:
        if rule.anchored:
            return rel_path == rule.pattern or rel_path.startswith(f"{rule.pattern}/")
        parts = rel_path.split("/")
        for idx in range(len(parts)):
            candidate = "/".join(parts[idx:])
            if candidate == rule.pattern or candidate.startswith(f"{rule.pattern}/"):
                return True
        return False
    path_obj = PurePosixPath(rel_path)

    if rule.anchored:
        return fnmatch.fnmatch(rel_path, rule.pattern)
    if rule.has_slash:
        return fnmatch.fnmatch(rel_path, rule.pattern) or fnmatch.fnmatch(rel_path, f"**/{rule.pattern}")
    if fnmatch.fnmatch(path_obj.name, rule.pattern):
        return True
    for parent in path_obj.parents:
        if parent == PurePosixPath("."):
            continue
        if fnmatch.fnmatch(parent.name, rule.pattern):
            return True
    return False


def is_ignored(rel_path: str, rules: list[IgnoreRule], is_dir: bool = False) -> bool:
    ignored = False
    for rule in rules:
        if _rule_matches(rule, rel_path, is_dir=is_dir):
            ignored = not rule.negated
    return ignored
