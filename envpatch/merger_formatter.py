from __future__ import annotations

import sys
from typing import Optional

from envpatch.merger import MergeResult

_RESET = "\033[0m"
_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"
_BOLD = "\033[1m"


def _colorize(text: str, color: str, use_color: bool = True) -> str:
    if not use_color:
        return text
    return f"{color}{text}{_RESET}"


def format_merge_report(
    result: MergeResult,
    use_color: bool = True,
    show_skipped: bool = False,
) -> str:
    if not result.has_changes() and not result.skipped:
        return _colorize("Files are identical — nothing to merge.", _CYAN, use_color)

    lines = []

    for key in result.added:
        label = _colorize("+ ADDED", _GREEN, use_color)
        lines.append(f"  {label}    {key}")

    for key in result.modified:
        label = _colorize("~ MODIFIED", _YELLOW, use_color)
        lines.append(f"  {label} {key}")

    for key in result.removed:
        label = _colorize("- REMOVED", _RED, use_color)
        lines.append(f"  {label}  {key}")

    if show_skipped:
        for key in result.skipped:
            label = _colorize("  SKIPPED", _CYAN, use_color)
            lines.append(f"  {label}  {key}")

    return "\n".join(lines) if lines else _colorize("No visible changes.", _CYAN, use_color)


def format_merge_summary(
    result: MergeResult,
    use_color: bool = True,
) -> str:
    summary = result.summary()
    if result.has_changes():
        return _colorize(summary, _BOLD, use_color)
    return _colorize(summary, _CYAN, use_color)
