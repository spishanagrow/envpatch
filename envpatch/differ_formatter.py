"""Rich formatter for diff output produced by envpatch.differ."""
from __future__ import annotations

import sys

from envpatch.differ import DiffEntry, ChangeType

_COLORS = {
    "green": "\033[32m",
    "red": "\033[31m",
    "yellow": "\033[33m",
    "cyan": "\033[36m",
    "bold": "\033[1m",
    "reset": "\033[0m",
}


def _colorize(text: str, color: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"{_COLORS.get(color, '')}{text}{_COLORS['reset']}"


def format_diff_entry(entry: DiffEntry, *, show_values: bool = False) -> str:
    """Format a single DiffEntry as a coloured line."""
    if entry.change_type == ChangeType.ADDED:
        prefix = _colorize("+", "green")
        key_str = _colorize(entry.key, "green")
        value_str = f" = {entry.masked_new}" if show_values else ""
        return f"  {prefix} {key_str}{value_str}"
    if entry.change_type == ChangeType.REMOVED:
        prefix = _colorize("-", "red")
        key_str = _colorize(entry.key, "red")
        value_str = f" = {entry.masked_old}" if show_values else ""
        return f"  {prefix} {key_str}{value_str}"
    if entry.change_type == ChangeType.MODIFIED:
        prefix = _colorize("~", "yellow")
        key_str = _colorize(entry.key, "yellow")
        if show_values:
            return f"  {prefix} {key_str} : {entry.masked_old!r} -> {entry.masked_new!r}"
        return f"  {prefix} {key_str}"
    # UNCHANGED
    prefix = " "
    return f"  {prefix} {entry.key}"


def format_diff_report(
    entries: list[DiffEntry],
    *,
    show_unchanged: bool = False,
    show_values: bool = False,
) -> str:
    """Render all diff entries as a multi-line report string."""
    visible = [
        e for e in entries
        if show_unchanged or e.change_type != ChangeType.UNCHANGED
    ]
    if not visible:
        return _colorize("No differences found.", "cyan")
    return "\n".join(format_diff_entry(e, show_values=show_values) for e in visible)


def format_diff_stats(entries: list[DiffEntry]) -> str:
    """Return a compact statistics line for a diff."""
    added = sum(1 for e in entries if e.change_type == ChangeType.ADDED)
    removed = sum(1 for e in entries if e.change_type == ChangeType.REMOVED)
    modified = sum(1 for e in entries if e.change_type == ChangeType.MODIFIED)
    parts = []
    if added:
        parts.append(_colorize(f"+{added}", "green"))
    if removed:
        parts.append(_colorize(f"-{removed}", "red"))
    if modified:
        parts.append(_colorize(f"~{modified}", "yellow"))
    if not parts:
        return _colorize("0 changes", "cyan")
    return "  ".join(parts)
