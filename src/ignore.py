from __future__ import annotations

from pathlib import Path

from pathspec import PathSpec


def load_ignore_rules(repo_root: Path) -> PathSpec:
    ignore_file = repo_root / ".gitignore"
    if not ignore_file.exists():
        return PathSpec.from_lines("gitignore", [])
    patterns = ignore_file.read_text(encoding="utf-8", errors="replace").splitlines()
    return PathSpec.from_lines("gitignore", patterns)


def is_ignored(rel_path: str, rules: PathSpec, is_dir: bool = False) -> bool:
    normalized = rel_path.strip("/")
    if not normalized:
        return False
    candidate = f"{normalized}/" if is_dir else normalized
    return rules.match_file(candidate)
