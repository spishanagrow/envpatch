"""Formatter for MergeResult output."""
from __future__ import annotations

import sys

from envpatch.merger import MergeResult
from envpatch.differ import ChangeType

_COLORS = {
    "green": "\033[32m",
    "red": "\033[31m",
    "yellow": "\033[33m",
    "cyan": "\033[36m",
    "reset": "\033[0m",
    "bold": "\033[1m",
}


def _colorize(text: str, color: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"{_COLORS.get(color, '')}{text}{_COLORS['reset']}"


def format_merge_report(result: MergeResult, *, show_values: bool = False) -> str:
    """Return a human-readable string describing each change in the merge."""
    if not result.has_changes():
        return _colorize("No changes applied — files are identical.", "cyan")

    lines: list[str] = []
    for entry in result.changes:
        key = entry.key
        if entry.change_type == ChangeType.ADDED:
            label = _colorize("+", "green")
            value_hint = f" = {entry.new_value}" if show_values and entry.new_value is not None else ""
            lines.append(f"  {label} {_colorize(key, 'green')}{value_hint}")
        elif entry.change_type == ChangeType.REMOVED:
            label = _colorize("-", "red")
            value_hint = f" = {entry.old_value}" if show_values and entry.old_value is not None else ""
            lines.append(f"  {label} {_colorize(key, 'red')}{value_hint}")
        elif entry.change_type == ChangeType.MODIFIED:
            label = _colorize("~", "yellow")
            if show_values:
                lines.append(
                    f"  {label} {_colorize(key, 'yellow')}"
                    f" : {entry.old_value!r} -> {entry.new_value!r}"
                )
            else:
                lines.append(f"  {label} {_colorize(key, 'yellow')}")

    return "\n".join(lines)


def format_merge_summary(result: MergeResult) -> str:
    """Return a one-line summary of the merge operation."""
    added = sum(1 for e in result.changes if e.change_type == ChangeType.ADDED)
    removed = sum(1 for e in result.changes if e.change_type == ChangeType.REMOVED)
    modified = sum(1 for e in result.changes if e.change_type == ChangeType.MODIFIED)

    parts = []
    if added:
        parts.append(_colorize(f"{added} added", "green"))
    if removed:
        parts.append(_colorize(f"{removed} removed", "red"))
    if modified:
        parts.append(_colorize(f"{modified} modified", "yellow"))
    if not parts:
        return _colorize("No changes.", "cyan")
    return "Merge summary: " + ", ".join(parts) + "."
