from __future__ import annotations

from pathlib import Path

from conftest import run_pygit


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def append(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(content)


def test_log_and_rev_parse(tmp_path: Path) -> None:
    run_pygit(tmp_path, "init", ".")
    write(tmp_path / "note.txt", "one\n")
    run_pygit(tmp_path, "add", "note.txt")
    run_pygit(tmp_path, "commit", "-m", "first")
    write(tmp_path / "note.txt", "two\n")
    run_pygit(tmp_path, "add", "note.txt")
    run_pygit(tmp_path, "commit", "-m", "second")

    log_lines = run_pygit(tmp_path, "log", "--oneline").stdout.strip().splitlines()
    assert len(log_lines) >= 2
    assert log_lines[0].endswith("second")
    assert log_lines[1].endswith("first")

    head = run_pygit(tmp_path, "rev-parse", "HEAD").stdout.strip()
    short = head[:8]
    resolved = run_pygit(tmp_path, "rev-parse", short).stdout.strip()
    assert len(head) == 40
    assert resolved == head


def test_branch_and_checkout(tmp_path: Path) -> None:
    run_pygit(tmp_path, "init", ".")
    write(tmp_path / "state.txt", "v1\n")
    run_pygit(tmp_path, "add", "state.txt")
    run_pygit(tmp_path, "commit", "-m", "c1")
    first = run_pygit(tmp_path, "rev-parse", "HEAD").stdout.strip()

    run_pygit(tmp_path, "branch", "feature")
    write(tmp_path / "state.txt", "v2\n")
    run_pygit(tmp_path, "add", "state.txt")
    run_pygit(tmp_path, "commit", "-m", "c2")
    second = run_pygit(tmp_path, "rev-parse", "HEAD").stdout.strip()

    run_pygit(tmp_path, "checkout", "feature")
    status = run_pygit(tmp_path, "status").stdout.splitlines()[0]
    assert status == "On branch feature"
    assert (tmp_path / "state.txt").read_text(encoding="utf-8").strip() == "v1"
    assert run_pygit(tmp_path, "rev-parse", "HEAD").stdout.strip() == first

    run_pygit(tmp_path, "checkout", second)
    detached = run_pygit(tmp_path, "status").stdout.splitlines()[0]
    assert detached.startswith("HEAD detached at ")
    assert (tmp_path / "state.txt").read_text(encoding="utf-8").strip() == "v2"
    assert run_pygit(tmp_path, "rev-parse", "HEAD").stdout.strip() == second


def test_checkout_blocks_dirty_tree(tmp_path: Path) -> None:
    run_pygit(tmp_path, "init", ".")
    write(tmp_path / "a.txt", "base\n")
    run_pygit(tmp_path, "add", "a.txt")
    run_pygit(tmp_path, "commit", "-m", "base")
    append(tmp_path / "a.txt", "dirty\n")

    proc = run_pygit(tmp_path, "checkout", "HEAD", check=False)
    assert proc.returncode == 1
    assert "cannot checkout with local changes" in proc.stderr


def test_rm_and_restore_staged(tmp_path: Path) -> None:
    run_pygit(tmp_path, "init", ".")
    write(tmp_path / "a.txt", "one\n")
    write(tmp_path / "b.txt", "base\n")
    run_pygit(tmp_path, "add", "a.txt", "b.txt")
    run_pygit(tmp_path, "commit", "-m", "base")

    write(tmp_path / "a.txt", "two\n")
    run_pygit(tmp_path, "add", "a.txt")
    run_pygit(tmp_path, "restore", "--staged", "a.txt")
    status_after_restore = run_pygit(tmp_path, "status").stdout
    assert "modified: a.txt" in status_after_restore

    write(tmp_path / "c.txt", "new\n")
    run_pygit(tmp_path, "add", "c.txt")
    run_pygit(tmp_path, "restore", "--staged", "c.txt")
    status_after_unstage_new = run_pygit(tmp_path, "status").stdout
    assert "Untracked files:" in status_after_unstage_new
    assert "c.txt" in status_after_unstage_new

    run_pygit(tmp_path, "rm", "b.txt")
    assert not (tmp_path / "b.txt").exists()
    status_after_rm = run_pygit(tmp_path, "status").stdout
    assert "staged:   b.txt" in status_after_rm


def test_gitignore_affects_add_and_status(tmp_path: Path) -> None:
    run_pygit(tmp_path, "init", ".")
    write(tmp_path / ".gitignore", "*.log\nbuild/\n")
    write(tmp_path / "keep.txt", "tracked\n")
    write(tmp_path / "debug.log", "noise\n")
    write(tmp_path / "build" / "out.txt", "artifact\n")

    run_pygit(tmp_path, "add", ".")
    ls_files = run_pygit(tmp_path, "ls-files").stdout
    assert ".gitignore" in ls_files
    assert "keep.txt" in ls_files
    assert "debug.log" not in ls_files
    assert "build/out.txt" not in ls_files

    status = run_pygit(tmp_path, "status").stdout
    assert "debug.log" not in status
    assert "build/out.txt" not in status


def test_tracked_paths_remain_visible_after_ignore_rule(tmp_path: Path) -> None:
    run_pygit(tmp_path, "init", ".")
    write(tmp_path / "logs" / "app.log", "base\n")
    run_pygit(tmp_path, "add", "logs/app.log")
    run_pygit(tmp_path, "commit", "-m", "track log")

    write(tmp_path / ".gitignore", "*.log\n")
    run_pygit(tmp_path, "add", ".gitignore")
    run_pygit(tmp_path, "commit", "-m", "ignore logs")

    append(tmp_path / "logs" / "app.log", "changed\n")
    status = run_pygit(tmp_path, "status").stdout
    assert "modified: logs/app.log" in status

