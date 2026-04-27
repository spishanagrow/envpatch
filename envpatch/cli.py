"""Command-line interface for envpatch."""

import argparse
import sys
from pathlib import Path

from envpatch.differ import diff_env_files
from envpatch.formatter import format_diff, format_summary
from envpatch.merger import merge_env_files
from envpatch.parser import parse_env_string


def _read_file(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)


def cmd_diff(args: argparse.Namespace) -> None:
    base = parse_env_string(_read_file(args.base))
    target = parse_env_string(_read_file(args.target))
    diff = diff_env_files(base, target)

    if not diff:
        print("No differences found.")
        return

    print(format_diff(diff, mask_secrets=not args.show_secrets))
    print()
    print(format_summary(diff))


def cmd_merge(args: argparse.Namespace) -> None:
    base = parse_env_string(_read_file(args.base))
    patch = parse_env_string(_read_file(args.patch))

    result = merge_env_files(
        base,
        patch,
        skip_secrets=args.skip_secrets,
        dry_run=args.dry_run,
    )

    if args.dry_run:
        print("[dry-run] Merge preview:")
        print(result.as_string())
        print(f"\nApplied: {len(result.applied)} | Skipped: {len(result.skipped)}")
        return

    output_path = Path(args.output) if args.output else Path(args.base)
    output_path.write_text(result.as_string() + "\n", encoding="utf-8")
    print(f"Merged into {output_path}")
    print(f"Applied: {len(result.applied)} | Skipped: {len(result.skipped)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envpatch",
        description="Safely diff and merge .env files across environments.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    diff_p = sub.add_parser("diff", help="Show differences between two .env files")
    diff_p.add_argument("base", help="Base .env file")
    diff_p.add_argument("target", help="Target .env file")
    diff_p.add_argument("--show-secrets", action="store_true", help="Display secret values unmasked")
    diff_p.set_defaults(func=cmd_diff)

    merge_p = sub.add_parser("merge", help="Merge a patch .env into a base .env")
    merge_p.add_argument("base", help="Base .env file")
    merge_p.add_argument("patch", help="Patch .env file to apply")
    merge_p.add_argument("-o", "--output", help="Output file (defaults to base)")
    merge_p.add_argument("--skip-secrets", action="store_true", help="Skip secret keys during merge")
    merge_p.add_argument("--dry-run", action="store_true", help="Preview merge without writing")
    merge_p.set_defaults(func=cmd_merge)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
