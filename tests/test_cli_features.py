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


def test_commit_amend_replaces_head_commit(tmp_path: Path) -> None:
    run_pygit(tmp_path, "init", ".")
    write(tmp_path / "note.txt", "v1\n")
    run_pygit(tmp_path, "add", "note.txt")
    run_pygit(tmp_path, "commit", "-m", "first")
    first = run_pygit(tmp_path, "rev-parse", "HEAD").stdout.strip()

    write(tmp_path / "note.txt", "v2\n")
    run_pygit(tmp_path, "add", "note.txt")
    run_pygit(tmp_path, "commit", "--amend", "-m", "first amended")
    amended = run_pygit(tmp_path, "rev-parse", "HEAD").stdout.strip()
    assert amended != first

    oneline = run_pygit(tmp_path, "log", "--oneline", "-n", "1").stdout.strip()
    assert oneline.endswith("first amended")

    commit_body = run_pygit(tmp_path, "cat-file", "-p", "HEAD").stdout
    assert "parent " not in commit_body


def test_commit_requires_message_without_amend(tmp_path: Path) -> None:
    run_pygit(tmp_path, "init", ".")
    write(tmp_path / "note.txt", "x\n")
    run_pygit(tmp_path, "add", "note.txt")
    proc = run_pygit(tmp_path, "commit", check=False)
    assert proc.returncode == 1
    assert "commit message is required" in proc.stderr


def test_reset_soft_and_mixed(tmp_path: Path) -> None:
    run_pygit(tmp_path, "init", ".")
    write(tmp_path / "f.txt", "v1\n")
    run_pygit(tmp_path, "add", "f.txt")
    run_pygit(tmp_path, "commit", "-m", "c1")
    c1 = run_pygit(tmp_path, "rev-parse", "HEAD").stdout.strip()

    write(tmp_path / "f.txt", "v2\n")
    run_pygit(tmp_path, "add", "f.txt")
    run_pygit(tmp_path, "commit", "-m", "c2")
    c2 = run_pygit(tmp_path, "rev-parse", "HEAD").stdout.strip()
    assert c1 != c2

    run_pygit(tmp_path, "reset", "--soft", c1)
    assert run_pygit(tmp_path, "rev-parse", "HEAD").stdout.strip() == c1
    soft_status = run_pygit(tmp_path, "status").stdout
    assert "staged:   f.txt" in soft_status

    run_pygit(tmp_path, "reset", "--mixed", c1)
    mixed_status = run_pygit(tmp_path, "status").stdout
    assert "Changes to be committed:" not in mixed_status
    assert "modified: f.txt" in mixed_status


def test_reset_rejects_non_commit_revision(tmp_path: Path) -> None:
    run_pygit(tmp_path, "init", ".")
    write(tmp_path / "blob.txt", "blob\n")
    blob = run_pygit(tmp_path, "hash-object", "-w", "blob.txt").stdout.strip()
    proc = run_pygit(tmp_path, "reset", blob, check=False)
    assert proc.returncode == 1
    assert "does not resolve to a commit" in proc.stderr
