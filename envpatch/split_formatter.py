"""Formatter for SplitResult output."""
from __future__ import annotations

from typing import Optional

from envpatch.splitter import SplitResult

_COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "cyan": "\033[36m",
    "yellow": "\033[33m",
    "green": "\033[32m",
    "dim": "\033[2m",
}


def _colorize(text: str, color: str, use_color: bool = True) -> str:
    if not use_color:
        return text
    return f"{_COLORS.get(color, '')}{text}{_COLORS['reset']}"


def format_split_report(result: SplitResult, use_color: bool = True) -> str:
    if not result.buckets and not result.unmatched.entries:
        return _colorize("No entries to split.", "dim", use_color)

    lines = []
    for name, env_file in result.buckets.items():
        header = _colorize(f"[{name}]", "cyan", use_color)
        lines.append(header)
        for entry in env_file.entries:
            key_str = _colorize(entry.key or "", "bold", use_color)
            lines.append(f"  {key_str}={entry.value}")

    if result.unmatched.entries:
        header = _colorize("[unmatched]", "yellow", use_color)
        lines.append(header)
        for entry in result.unmatched.entries:
            key_str = _colorize(entry.key or "", "dim", use_color)
            lines.append(f"  {key_str}={entry.value}")

    return "\n".join(lines)


def format_split_summary(result: SplitResult, use_color: bool = True) -> str:
    total = result.total_matched() + result.total_unmatched()
    matched = result.total_matched()
    buckets = len(result.buckets)
    msg = (
        f"Split {total} entr{'y' if total == 1 else 'ies'} "
        f"into {buckets} bucket{'s' if buckets != 1 else ''} "
        f"({matched} matched, {result.total_unmatched()} unmatched)."
    )
    return _colorize(msg, "green", use_color)
