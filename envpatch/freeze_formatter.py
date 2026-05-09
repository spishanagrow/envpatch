"""freeze_formatter.py — human-readable output for FreezeResult."""
from __future__ import annotations

from envpatch.freezer import FreezeResult


def _colorize(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def format_freeze_report(result: FreezeResult, *, color: bool = True) -> str:
    if not result.frozen and not result.already_frozen:
        msg = "No entries to freeze."
        return _colorize(msg, "33") if color else msg

    lines: list[str] = []
    for entry in result.frozen:
        label = _colorize("[frozen]", "36") if color else "[frozen]"
        lines.append(f"  {label} {entry.key}")
    for entry in result.already_frozen:
        label = _colorize("[already frozen]", "90") if color else "[already frozen]"
        lines.append(f"  {label} {entry.key}")
    for entry in result.skipped:
        label = _colorize("[skipped]", "33") if color else "[skipped]"
        lines.append(f"  {label} {entry.key}")

    header = _colorize("Freeze report:", "1") if color else "Freeze report:"
    return header + "\n" + "\n".join(lines)


def format_freeze_summary(result: FreezeResult, *, color: bool = True) -> str:
    parts = [
        f"frozen={result.frozen_count}",
        f"already_frozen={result.already_frozen_count}",
        f"skipped={len(result.skipped)}",
    ]
    summary = "  ".join(parts)
    return _colorize(summary, "32") if color else summary
