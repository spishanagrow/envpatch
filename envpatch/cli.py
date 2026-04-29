"""CLI entry-point for envpatch."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envpatch.parser import parse_env_string
from envpatch.differ import diff_env_files
from envpatch.formatter import format_diff, format_summary
from envpatch.merger import merge_env_files
from envpatch.validator import validate_env_file
from envpatch.snapshotter import take_snapshot, snapshots_differ, changed_keys


def _read_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def cmd_diff(args: argparse.Namespace) -> int:
    base = parse_env_string(_read_file(args.base))
    target = parse_env_string(_read_file(args.target))
    entries = diff_env_files(base, target)
    if args.summary:
        print(format_summary(entries))
    else:
        print(format_diff(entries, color=not args.no_color))
    return 0


def cmd_merge(args: argparse.Namespace) -> int:
    base = parse_env_string(_read_file(args.base))
    patch = parse_env_string(_read_file(args.patch))
    result = merge_env_files(base, patch)
    if args.output:
        Path(args.output).write_text(result.content, encoding="utf-8")
    else:
        print(result.content, end="")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    env_file = parse_env_string(_read_file(args.file))
    result = validate_env_file(env_file)
    for issue in result.issues:
        print(str(issue))
    return 1 if result.has_errors() else 0


def cmd_snapshot(args: argparse.Namespace) -> int:
    """Capture a redacted snapshot and optionally compare with a previous one."""
    env_file = parse_env_string(_read_file(args.file))
    snap = take_snapshot(env_file, label=args.label)

    if args.compare:
        try:
            previous_raw = _read_file(args.compare)
            from envpatch.snapshotter import Snapshot
            previous = Snapshot.from_json(previous_raw)
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as exc:
            print(f"error: cannot load comparison snapshot: {exc}", file=sys.stderr)
            return 2

        if snapshots_differ(previous, snap):
            diff = changed_keys(previous, snap)
            print(f"Snapshots differ ({len(diff)} key(s) changed):")
            for key, (old_val, new_val) in sorted(diff.items()):
                old_str = old_val if old_val is not None else "<absent>"
                new_str = new_val if new_val is not None else "<absent>"
                print(f"  {key}: {old_str!r} -> {new_str!r}")
            return 1
        else:
            print("Snapshots are identical.")
            return 0

    output = snap.to_json()
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Snapshot saved to {args.output}")
    else:
        print(output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envpatch",
        description="Safely diff and merge .env files across environments.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # diff
    p_diff = sub.add_parser("diff", help="Show differences between two .env files.")
    p_diff.add_argument("base")
    p_diff.add_argument("target")
    p_diff.add_argument("--summary", action="store_true")
    p_diff.add_argument("--no-color", action="store_true")
    p_diff.set_defaults(func=cmd_diff)

    # merge
    p_merge = sub.add_parser("merge", help="Apply a patch .env onto a base .env.")
    p_merge.add_argument("base")
    p_merge.add_argument("patch")
    p_merge.add_argument("-o", "--output")
    p_merge.set_defaults(func=cmd_merge)

    # validate
    p_val = sub.add_parser("validate", help="Validate a .env file for common issues.")
    p_val.add_argument("file")
    p_val.set_defaults(func=cmd_validate)

    # snapshot
    p_snap = sub.add_parser("snapshot", help="Capture or compare a .env snapshot.")
    p_snap.add_argument("file", help=".env file to snapshot.")
    p_snap.add_argument("--label", default="snapshot", help="Human-readable label.")
    p_snap.add_argument("-o", "--output", help="Write snapshot JSON to this file.")
    p_snap.add_argument("--compare", metavar="SNAPSHOT_JSON",
                        help="Compare against a previously saved snapshot.")
    p_snap.set_defaults(func=cmd_snapshot)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
