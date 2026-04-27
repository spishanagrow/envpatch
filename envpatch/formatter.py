"""Format DiffResult objects for human-readable CLI output."""

from typing import Optional

from envpatch.differ import ChangeType, DiffEntry, DiffResult

ANSI_RESET = "\033[0m"
ANSI_GREEN = "\033[32m"
ANSI_RED = "\033[31m"
ANSI_YELLOW = "\033[33m"
ANSI_DIM = "\033[2m"


def _colorize(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{color}{text}{ANSI_RESET}"


def _format_value(value: Optional[str], masked: Optional[str]) -> str:
    if value is None:
        return ""
    display = masked if masked is not None else value
    return f"={display}"


def format_diff(result: DiffResult, use_color: bool = True, mask_secrets: bool = True) -> str:
    """Render a DiffResult as a human-readable unified-style diff string."""
    lines = []

    for entry in result.entries:
        key = entry.key
        old_val = entry.masked_old() if mask_secrets else entry.old_value
        new_val = entry.masked_new() if mask_secrets else entry.new_value

        if entry.change_type == ChangeType.ADDED:
            line = f"+ {key}{_format_value(entry.new_value, new_val)}"
            lines.append(_colorize(line, ANSI_GREEN, use_color))

        elif entry.change_type == ChangeType.REMOVED:
            line = f"- {key}{_format_value(entry.old_value, old_val)}"
            lines.append(_colorize(line, ANSI_RED, use_color))

        elif entry.change_type == ChangeType.MODIFIED:
            old_line = f"- {key}{_format_value(entry.old_value, old_val)}"
            new_line = f"+ {key}{_format_value(entry.new_value, new_val)}"
            lines.append(_colorize(old_line, ANSI_RED, use_color))
            lines.append(_colorize(new_line, ANSI_GREEN, use_color))

        elif entry.change_type == ChangeType.UNCHANGED:
            line = f"  {key}{_format_value(entry.old_value, old_val)}"
            lines.append(_colorize(line, ANSI_DIM, use_color))

    if not lines:
        return _colorize("No differences found.", ANSI_DIM, use_color)

    return "\n".join(lines)


def format_summary(result: DiffResult) -> str:
    """Return a one-line summary of the diff."""
    added = len(result.added())
    removed = len(result.removed())
    modified = len(result.modified())
    return f"Diff summary: +{added} added, -{removed} removed, ~{modified} modified"
