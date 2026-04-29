"""CLI entry-point for envpatch."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envpatch.parser import parse_env_string
from envpatch.differ import diff_files, format_diff
from envpatch.merger import merge_env_files
from envpatch.validator import validate_file
from envpatch.snapshotter import take_snapshot
from envpatch.scorer import score_file


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _read_file(path: str):
    text = Path(path).read_text(encoding="utf-8")
    return parse_env_string(text, source=path)


# ---------------------------------------------------------------------------
# sub-commands
# ---------------------------------------------------------------------------

def cmd_diff(args: argparse.Namespace) -> int:
    base = _read_file(args.base)
    target = _read_file(args.target)
    entries = diff_files(base, target)
    if not entries:
        print("No differences found.")
        return 0
    print(format_diff(entries, mask_secrets=not args.show_secrets))
    return 0


def cmd_merge(args: argparse.Namespace) -> int:
    base = _read_file(args.base)
    patch = _read_file(args.patch)
    result = merge_env_files(base, patch)
    out = Path(args.output) if args.output else None
    content = result.as_string()
    if out:
        out.write_text(content, encoding="utf-8")
        print(f"Merged file written to {out}")
    else:
        print(content)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    env = _read_file(args.file)
    result = validate_file(env)
    for issue in result.issues:
        print(str(issue))
    if result.has_errors():
        print("Validation failed.", file=sys.stderr)
        return 1
    print("Validation passed.")
    return 0


def cmd_snapshot(args: argparse.Namespace) -> int:
    env = _read_file(args.file)
    snap = take_snapshot(env, label=args.label)
    print(snap.to_json(indent=2))
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    env = _read_file(args.file)
    report = score_file(env)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(f"Score : {report.score}/100  ({report.grade})")
        print(f"Keys  : {report.total_keys} total, "
              f"{report.secret_keys} secret, "
              f"{report.placeholder_keys} placeholder, "
              f"{report.empty_keys} empty")
        if report.penalties:
            print("Penalties:")
            for p in report.penalties:
                print(f"  {p}")
    return 0


# ---------------------------------------------------------------------------
# parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envpatch",
        description="Safely diff and merge .env files.",
    )
    sub = parser.add_subparsers(dest="command")

    # diff
    p_diff = sub.add_parser("diff", help="Diff two .env files.")
    p_diff.add_argument("base")
    p_diff.add_argument("target")
    p_diff.add_argument("--show-secrets", action="store_true")

    # merge
    p_merge = sub.add_parser("merge", help="Merge a patch .env into a base .env.")
    p_merge.add_argument("base")
    p_merge.add_argument("patch")
    p_merge.add_argument("-o", "--output", default=None)

    # validate
    p_val = sub.add_parser("validate", help="Validate a .env file.")
    p_val.add_argument("file")

    # snapshot
    p_snap = sub.add_parser("snapshot", help="Take a snapshot of a .env file.")
    p_snap.add_argument("file")
    p_snap.add_argument("--label", default=None)

    # score
    p_score = sub.add_parser("score", help="Score a .env file for hygiene.")
    p_score.add_argument("file")
    p_score.add_argument("--json", action="store_true", help="Output as JSON.")

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    dispatch = {
        "diff": cmd_diff,
        "merge": cmd_merge,
        "validate": cmd_validate,
        "snapshot": cmd_snapshot,
        "score": cmd_score,
    }
    if args.command is None:
        parser.print_help()
        return 0
    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
