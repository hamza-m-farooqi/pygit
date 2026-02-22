from __future__ import annotations

import argparse
import sys

from commands import (
    cmd_add,
    cmd_branch,
    cmd_cat_file,
    cmd_checkout,
    cmd_commit,
    cmd_diff,
    cmd_hash_object,
    cmd_log,
    cmd_push,
    cmd_restore,
    cmd_rm,
    cmd_reset,
    cmd_remote,
    cmd_rev_parse,
    cmd_init,
    cmd_ls_files,
    cmd_status,
    cmd_write_tree,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pygit", description="Minimal Git-like utility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize a repository")
    init_parser.add_argument("path", help="Path to repository root")
    init_parser.set_defaults(func=cmd_init)

    hash_parser = subparsers.add_parser("hash-object", help="Hash file and optionally write object")
    hash_parser.add_argument("path", help="File to hash")
    hash_parser.add_argument("-t", "--type", default="blob", choices=["blob", "tree", "commit"])
    hash_parser.add_argument("-w", "--write", action="store_true")
    hash_parser.set_defaults(func=cmd_hash_object)

    cat_parser = subparsers.add_parser("cat-file", help="Inspect object contents")
    mode_group = cat_parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("-p", "--pretty", action="store_true", help="Pretty-print object")
    mode_group.add_argument("-t", "--type-only", action="store_true", help="Print object type")
    mode_group.add_argument("-s", "--size-only", action="store_true", help="Print object size")
    cat_parser.add_argument("object", help="Object id or prefix")
    cat_parser.set_defaults(func=cmd_cat_file)

    add_parser = subparsers.add_parser("add", help="Add paths to index")
    add_parser.add_argument("paths", nargs="+", help="Files or directories to stage")
    add_parser.set_defaults(func=cmd_add)

    ls_files_parser = subparsers.add_parser("ls-files", help="List index entries")
    ls_files_parser.add_argument("-s", "--stage", action="store_true", help="Show mode and object id")
    ls_files_parser.set_defaults(func=cmd_ls_files)

    status_parser = subparsers.add_parser("status", help="Show working tree status")
    status_parser.set_defaults(func=cmd_status)

    diff_parser = subparsers.add_parser("diff", help="Show unstaged differences")
    diff_parser.set_defaults(func=cmd_diff)

    write_tree_parser = subparsers.add_parser("write-tree", help="Write tree from index")
    write_tree_parser.set_defaults(func=cmd_write_tree)

    commit_parser = subparsers.add_parser("commit", help="Write commit object from index")
    commit_parser.add_argument("-m", "--message", help="Commit message")
    commit_parser.add_argument("--amend", action="store_true", help="Amend current HEAD commit")
    commit_parser.set_defaults(func=cmd_commit)

    log_parser = subparsers.add_parser("log", help="Show commit history")
    log_parser.add_argument("--oneline", action="store_true", help="Show one commit per line")
    log_parser.add_argument("-n", "--max-count", type=int, default=10, help="Limit number of commits")
    log_parser.set_defaults(func=cmd_log)

    rev_parse_parser = subparsers.add_parser("rev-parse", help="Resolve revision to full commit id")
    rev_parse_parser.add_argument("revision", help="Revision expression (HEAD, branch, short/full SHA)")
    rev_parse_parser.set_defaults(func=cmd_rev_parse)

    branch_parser = subparsers.add_parser("branch", help="List or create branches")
    branch_parser.add_argument("name", nargs="?", help="Branch name to create")
    branch_parser.set_defaults(func=cmd_branch)

    checkout_parser = subparsers.add_parser("checkout", help="Switch branches or detach HEAD at a commit")
    checkout_parser.add_argument("target", help="Branch name or revision")
    checkout_parser.set_defaults(func=cmd_checkout)

    rm_parser = subparsers.add_parser("rm", help="Remove tracked files from index and working tree")
    rm_parser.add_argument("paths", nargs="+", help="Tracked file or directory paths")
    rm_parser.set_defaults(func=cmd_rm)

    restore_parser = subparsers.add_parser("restore", help="Restore paths from HEAD into the index")
    restore_parser.add_argument("--staged", action="store_true", help="Restore staged content only")
    restore_parser.add_argument("paths", nargs="+", help="Pathspec to restore")
    restore_parser.set_defaults(func=cmd_restore)

    reset_parser = subparsers.add_parser("reset", help="Move HEAD to another commit")
    mode_group = reset_parser.add_mutually_exclusive_group()
    mode_group.add_argument("--soft", action="store_const", const="soft", dest="mode", help="Move HEAD only")
    mode_group.add_argument(
        "--mixed",
        action="store_const",
        const="mixed",
        dest="mode",
        help="Move HEAD and reset index to target tree",
    )
    reset_parser.set_defaults(mode="mixed")
    reset_parser.add_argument("revision", help="Target revision")
    reset_parser.set_defaults(func=cmd_reset)

    remote_parser = subparsers.add_parser("remote", help="Manage remotes")
    remote_subparsers = remote_parser.add_subparsers(dest="remote_cmd")

    remote_list_parser = remote_subparsers.add_parser("list", help="List remotes")
    remote_list_parser.add_argument("-v", "--verbose", action="store_true", help="Show remote URLs")
    remote_list_parser.set_defaults(func=cmd_remote)

    remote_add_parser = remote_subparsers.add_parser("add", help="Add a remote")
    remote_add_parser.add_argument("name", help="Remote name")
    remote_add_parser.add_argument("url", help="Remote URL")
    remote_add_parser.set_defaults(func=cmd_remote)

    remote_remove_parser = remote_subparsers.add_parser("remove", help="Remove a remote")
    remote_remove_parser.add_argument("name", help="Remote name")
    remote_remove_parser.set_defaults(func=cmd_remote)

    remote_get_url_parser = remote_subparsers.add_parser("get-url", help="Get remote URL")
    remote_get_url_parser.add_argument("name", help="Remote name")
    remote_get_url_parser.set_defaults(func=cmd_remote)

    remote_parser.set_defaults(func=cmd_remote, remote_cmd="list", verbose=False)

    push_parser = subparsers.add_parser("push", help="Push a branch to a remote")
    push_parser.add_argument("remote", nargs="?", help="Remote name (default: origin)")
    push_parser.add_argument("branch", nargs="?", help="Branch name (default: current branch)")
    push_parser.set_defaults(func=cmd_push)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
