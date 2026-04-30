"""Format GroupResult for terminal output."""
from __future__ import annotations

from typing import Optional

from envpatch.grouper import GroupResult

_COLORS = {
    "cyan": "\033[96m",
    "yellow": "\033[93m",
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
}


def _colorize(text: str, color: str, use_color: bool = True) -> str:
    if not use_color:
        return text
    code = _COLORS.get(color, "")
    return f"{code}{text}{_COLORS['reset']}"


def format_group_report(result: GroupResult, use_color: bool = True) -> str:
    """Return a multi-line string listing each group and its keys."""
    if not result.groups and not result.ungrouped:
        return "No entries to group."

    lines = []
    for name in result.group_names():
        header = _colorize(f"[{name}]", "cyan", use_color)
        lines.append(header)
        for entry in result.entries_for(name):
            lines.append(f"  {entry.key}")

    if result.ungrouped:
        header = _colorize("[ungrouped]", "yellow", use_color)
        lines.append(header)
        for entry in result.ungrouped:
            lines.append(_colorize(f"  {entry.key}", "dim", use_color))

    return "\n".join(lines)


def format_group_summary(result: GroupResult, use_color: bool = True) -> str:
    """Return a single-line summary of the grouping result."""
    count = len(result.groups)
    total = result.total_grouped()
    ungrouped = len(result.ungrouped)
    msg = f"{count} group(s), {total} grouped key(s), {ungrouped} ungrouped."
    return _colorize(msg, "bold", use_color)
