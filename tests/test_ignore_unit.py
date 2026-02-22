from __future__ import annotations

from pathlib import Path

from ignore import is_ignored, load_ignore_rules


def test_ignore_rule_matching(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("*.log\nbuild/\n!build/keep.log\n", encoding="utf-8")
    rules = load_ignore_rules(tmp_path)

    assert is_ignored("debug.log", rules)
    assert is_ignored("build/out.txt", rules)
    assert not is_ignored("build/keep.log", rules)
    assert not is_ignored("src/main.py", rules)


def test_ignore_gitwildmatch_features(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("**/*.tmp\n\\#notes.txt\n", encoding="utf-8")
    rules = load_ignore_rules(tmp_path)

    assert is_ignored("a.tmp", rules)
    assert is_ignored("nested/deep/file.tmp", rules)
    assert is_ignored("#notes.txt", rules)
    assert not is_ignored("notes.txt", rules)
