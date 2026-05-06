"""Format TransformResult objects for CLI output."""

from __future__ import annotations

import sys

from envpatch.transformer import TransformResult


def _colorize(text: str, code: str) -> str:
    if sys.stdout.isatty():
        return f"\033[{code}m{text}\033[0m"
    return text


def format_transform_report(result: TransformResult, *, show_skipped: bool = False) -> str:
    if not result.transformed_keys:
        return _colorize("No keys were transformed.", "33")

    lines = []
    for key in result.transformed_keys:
        label = _colorize("TRANSFORMED", "36")
        lines.append(f"  {label}  {key}")

    if show_skipped:
        for key in result.skipped_keys:
            label = _colorize("SKIPPED", "90")
            lines.append(f"  {label}     {key}")

    return "\n".join(lines)


def format_transform_summary(result: TransformResult) -> str:
    parts = []
    if result.transformed_count():
        parts.append(
            _colorize(f"{result.transformed_count()} transformed", "36")
        )
    if result.skipped_count():
        parts.append(
            _colorize(f"{result.skipped_count()} skipped", "90")
        )
    return ", ".join(parts) if parts else _colorize("nothing to do", "33")
