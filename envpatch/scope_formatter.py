"""Terminal formatter for ScopeResult output."""
from __future__ import annotations

import sys

from envpatch.scoper import ScopeResult

_COLORS = {
    "green": "\033[32m",
    "yellow": "\033[33m",
    "cyan": "\033[36m",
    "dim": "\033[2m",
    "reset": "\033[0m",
}


def _colorize(text: str, color: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"{_COLORS.get(color, '')}{text}{_COLORS['reset']}"


def format_scope_report(result: ScopeResult, *, show_excluded: bool = False) -> str:
    if not result.entries:
        return _colorize(f"No entries visible for scope '{result.scope}'.", "yellow")

    lines: list[str] = []
    lines.append(_colorize(f"# Scope: {result.scope}", "cyan"))

    for entry in result.universal:
        lines.append(_colorize(f"  {entry.key}={entry.value}", "dim"))

    for entry in result.matched:
        lines.append(_colorize(f"  {entry.key}={entry.value}", "green"))

    if show_excluded and result.excluded:
        lines.append(_colorize("# Excluded:", "yellow"))
        for entry in result.excluded:
            lines.append(_colorize(f"  # {entry.key}", "dim"))

    return "\n".join(lines)


def format_scope_summary(result: ScopeResult) -> str:
    return _colorize(result.summary(), "cyan")


def format_all_scopes(scopes: list[str]) -> str:
    if not scopes:
        return _colorize("No scopes declared in file.", "yellow")
    lines = [_colorize("Declared scopes:", "cyan")]
    for s in scopes:
        lines.append(f"  - {s}")
    return "\n".join(lines)
