"""Human-readable formatting for FilterResult."""

from __future__ import annotations

import sys

from envpatch.filter import FilterResult
from envpatch.differ import is_secret

_RESET = "\033[0m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"
_DIM = "\033[2m"


def _colorize(text: str, code: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"{code}{text}{_RESET}"


def format_filter_report(result: FilterResult, *, show_excluded: bool = False) -> str:
    lines: list[str] = []

    if not result.matched:
        lines.append(_colorize("No entries matched the filter.", _YELLOW))
        return "\n".join(lines)

    lines.append(_colorize(f"Matched {result.matched_count} entries:", _CYAN))
    for entry in result.matched:
        secret_tag = _colorize(" [secret]", _YELLOW) if is_secret(entry.key) else ""
        lines.append(f"  {_colorize(entry.key, _GREEN)}{secret_tag}")

    if show_excluded and result.excluded:
        lines.append("")
        lines.append(_colorize(f"Excluded {result.excluded_count} entries:", _DIM))
        for entry in result.excluded:
            lines.append(f"  {_colorize(entry.key, _DIM)}")

    return "\n".join(lines)


def format_filter_summary(result: FilterResult) -> str:
    return _colorize(result.summary(), _CYAN)
