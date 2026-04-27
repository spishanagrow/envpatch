"""Command-line interface for envpatch."""

import argparse
import sys
from pathlib import Path

from envpatch.differ import diff_env_files
from envpatch.formatter import format_diff, format_summary
from envpatch.merger import merge_env_files, as_string
from envpatch.parser import parse_env_string
from envpatch.validator import validate_env_file


def _read_file(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"Error reading {path}: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_diff(args: argparse.Namespace) -> int:
    base_text = _read_file(args.base)
    target_text = _read_file(args.target)
    base_file = parse_env_string(base_text)
    target_file = parse_env_string(target_text)
    entries = diff_env_files(base_file, target_file)
    print(format_diff(entries, mask_secrets=not args.show_secrets))
    print(format_summary(entries))
    return 0


def cmd_merge(args: argparse.Namespace) -> int:
    base_text = _read_file(args.base)
    patch_text = _read_file(args.patch)
    base_file = parse_env_string(base_text)
    patch_file = parse_env_string(patch_text)
    result = merge_env_files(base_file, patch_file)
    output = as_string(result.merged)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Merged env written to {args.output}")
    else:
        print(output)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    text = _read_file(args.file)
    env_file = parse_env_string(text)
    result = validate_env_file(env_file)
    if not result.issues:
        print(f"{args.file}: OK (no issues found)")
        return 0
    for issue in result.issues:
        print(str(issue))
    if result.has_errors:
        print(f"\n{args.file}: FAILED ({len(result.issues)} issue(s) found)", file=sys.stderr)
        return 1
    print(f"\n{args.file}: {len(result.issues)} warning(s)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envpatch",
        description="Safely diff and merge .env files across environments.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # diff sub-command
    diff_parser = subparsers.add_parser("diff", help="Show differences between two .env files")
    diff_parser.add_argument("base", help="Base .env file")
    diff_parser.add_argument("target", help="Target .env file")
    diff_parser.add_argument("--show-secrets", action="store_true", help="Reveal secret values")
    diff_parser.set_defaults(func=cmd_diff)

    # merge sub-command
    merge_parser = subparsers.add_parser("merge", help="Apply a patch .env onto a base .env")
    merge_parser.add_argument("base", help="Base .env file")
    merge_parser.add_argument("patch", help="Patch .env file")
    merge_parser.add_argument("-o", "--output", help="Write result to this file")
    merge_parser.set_defaults(func=cmd_merge)

    # validate sub-command
    validate_parser = subparsers.add_parser("validate", help="Validate a .env file for issues")
    validate_parser.add_argument("file", help=".env file to validate")
    validate_parser.set_defaults(func=cmd_validate)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
