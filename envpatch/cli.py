"""CLI entry point for envpatch."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from envpatch.parser import parse_env_string
from envpatch.differ import diff_env_files
from envpatch.formatter import format_diff, format_summary
from envpatch.merger import merge_env_files
from envpatch.validator import validate_env_file
from envpatch.auditor import AuditAction, AuditLog, make_entry

_audit_log = AuditLog()


def _read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def cmd_diff(args: argparse.Namespace) -> int:
    base = parse_env_string(_read_file(args.base))
    target = parse_env_string(_read_file(args.target))
    diffs = diff_env_files(base, target)
    if args.summary:
        print(format_summary(diffs))
    else:
        print(format_diff(diffs, color=not args.no_color))
    _audit_log.record(
        make_entry(AuditAction.DIFF, args.base, args.target, changes=len(diffs))
    )
    if args.audit_log:
        _audit_log.save(args.audit_log)
    return 0


def cmd_merge(args: argparse.Namespace) -> int:
    base = parse_env_string(_read_file(args.base))
    patch = parse_env_string(_read_file(args.patch))
    result = merge_env_files(base, patch)
    output = result.as_string()
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output)
    else:
        print(output, end="")
    _audit_log.record(
        make_entry(
            AuditAction.MERGE,
            args.base,
            args.patch,
            keys_added=len(result.added),
            keys_removed=len(result.removed),
            keys_modified=len(result.modified),
        )
    )
    if args.audit_log:
        _audit_log.save(args.audit_log)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    env_file = parse_env_string(_read_file(args.file))
    result = validate_env_file(env_file)
    for issue in result.issues:
        print(str(issue), file=sys.stderr)
    _audit_log.record(
        make_entry(
            AuditAction.VALIDATE,
            args.file,
            issues=len(result.issues),
        )
    )
    if args.audit_log:
        _audit_log.save(args.audit_log)
    return 1 if result.has_errors() else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envpatch",
        description="Safely diff and merge .env files across environments.",
    )
    parser.add_argument(
        "--audit-log", metavar="PATH", help="Append audit entry to JSON log file."
    )

    sub = parser.add_subparsers(dest="command")

    diff_p = sub.add_parser("diff", help="Show differences between two .env files.")
    diff_p.add_argument("base", help="Base .env file")
    diff_p.add_argument("target", help="Target .env file")
    diff_p.add_argument("--summary", action="store_true", help="Print summary only")
    diff_p.add_argument("--no-color", action="store_true", help="Disable color output")
    diff_p.set_defaults(func=cmd_diff)

    merge_p = sub.add_parser("merge", help="Merge a patch .env into a base .env.")
    merge_p.add_argument("base", help="Base .env file")
    merge_p.add_argument("patch", help="Patch .env file")
    merge_p.add_argument("-o", "--output", help="Output file (default: stdout)")
    merge_p.set_defaults(func=cmd_merge)

    val_p = sub.add_parser("validate", help="Validate a .env file for common issues.")
    val_p.add_argument("file", help=".env file to validate")
    val_p.set_defaults(func=cmd_validate)

    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
