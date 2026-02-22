from __future__ import annotations

import argparse
import sys

from commands import (
    cmd_add,
    cmd_cat_file,
    cmd_commit,
    cmd_diff,
    cmd_hash_object,
    cmd_log,
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
    commit_parser.add_argument("-m", "--message", required=True, help="Commit message")
    commit_parser.set_defaults(func=cmd_commit)

    log_parser = subparsers.add_parser("log", help="Show commit history")
    log_parser.add_argument("--oneline", action="store_true", help="Show one commit per line")
    log_parser.add_argument("-n", "--max-count", type=int, default=10, help="Limit number of commits")
    log_parser.set_defaults(func=cmd_log)

    rev_parse_parser = subparsers.add_parser("rev-parse", help="Resolve revision to full commit id")
    rev_parse_parser.add_argument("revision", help="Revision expression (HEAD, branch, short/full SHA)")
    rev_parse_parser.set_defaults(func=cmd_rev_parse)

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
