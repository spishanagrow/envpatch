"""Format :class:`LintReport` output for the terminal."""
from __future__ import annotations

from typing import List

from envpatch.linter import LintReport, LintIssue, LintCode

_COLORS = {
    "red": "\033[31m",
    "yellow": "\033[33m",
    "green": "\033[32m",
    "reset": "\033[0m",
    "bold": "\033[1m",
}

_SEVERITY_COLOR: dict[LintCode, str] = {
    LintCode.DUPLICATE_KEY: "red",
    LintCode.KEY_HAS_SPACES: "red",
    LintCode.KEY_NOT_UPPERCASE: "yellow",
    LintCode.VALUE_HAS_TRAILING_SPACE: "yellow",
    LintCode.INCONSISTENT_QUOTE_STYLE: "yellow",
}


def _colorize(text: str, color: str, use_color: bool = True) -> str:
    if not use_color:
        return text
    return f"{_COLORS.get(color, '')}{text}{_COLORS['reset']}"


def _format_issue(issue: LintIssue, use_color: bool = True) -> str:
    color = _SEVERITY_COLOR.get(issue.code, "yellow")
    code_str = _colorize(issue.code.value, color, use_color)
    location = _colorize(f"line {issue.line}", "bold", use_color)
    return f"  {code_str}  {location}  {issue.key}: {issue.message}"


def format_lint_report(report: LintReport, use_color: bool = True) -> str:
    """Return a human-readable string for *report*."""
    if not report.has_issues:
        ok = _colorize("✔ No lint issues found.", "green", use_color)
        return ok

    lines: List[str] = [
        _colorize(f"Found {len(report.issues)} lint issue(s):", "bold", use_color)
    ]
    for issue in report.issues:
        lines.append(_format_issue(issue, use_color))
    return "\n".join(lines)


def format_lint_summary(report: LintReport, use_color: bool = True) -> str:
    """Return a one-line summary suitable for CLI exit messages."""
    count = len(report.issues)
    if count == 0:
        return _colorize("lint: OK", "green", use_color)
    color = "red" if any(
        i.code in (LintCode.DUPLICATE_KEY, LintCode.KEY_HAS_SPACES)
        for i in report.issues
    ) else "yellow"
    return _colorize(f"lint: {count} issue(s)", color, use_color)
