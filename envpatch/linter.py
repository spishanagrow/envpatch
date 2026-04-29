"""Lint .env files for style and consistency issues."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List

from envpatch.parser import EnvFile, EnvEntry


class LintCode(str, Enum):
    KEY_NOT_UPPERCASE = "KEY_NOT_UPPERCASE"
    KEY_HAS_SPACES = "KEY_HAS_SPACES"
    VALUE_HAS_TRAILING_SPACE = "VALUE_HAS_TRAILING_SPACE"
    DUPLICATE_KEY = "DUPLICATE_KEY"
    INCONSISTENT_QUOTE_STYLE = "INCONSISTENT_QUOTE_STYLE"


@dataclass
class LintIssue:
    code: LintCode
    key: str
    line: int
    message: str

    def __str__(self) -> str:
        return f"[{self.code.value}] line {self.line} ({self.key}): {self.message}"


@dataclass
class LintReport:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return len(self.issues) > 0

    def by_code(self, code: LintCode) -> List[LintIssue]:
        return [i for i in self.issues if i.code == code]

    def to_dict(self) -> dict:
        return {
            "issue_count": len(self.issues),
            "issues": [
                {"code": i.code.value, "key": i.key, "line": i.line, "message": i.message}
                for i in self.issues
            ],
        }


def _detect_quote_style(entries: List[EnvEntry]) -> str | None:
    """Return dominant quote style or None if mixed/absent."""
    quoted = [e for e in entries if e.value.startswith(("'", '"'))]
    if not quoted:
        return None
    double = sum(1 for e in quoted if e.value.startswith('"'))
    single = len(quoted) - double
    return '"' if double >= single else "'"


def lint_file(env_file: EnvFile) -> LintReport:
    """Run all lint checks on *env_file* and return a :class:`LintReport`."""
    issues: List[LintIssue] = []
    seen_keys: dict[str, int] = {}
    dominant_quote = _detect_quote_style(env_file.entries)

    for entry in env_file.entries:
        key, value, lineno = entry.key, entry.value, entry.line

        if key != key.upper():
            issues.append(LintIssue(LintCode.KEY_NOT_UPPERCASE, key, lineno,
                                    "Key should be uppercase"))

        if " " in key:
            issues.append(LintIssue(LintCode.KEY_HAS_SPACES, key, lineno,
                                    "Key must not contain spaces"))

        if value != value.rstrip():
            issues.append(LintIssue(LintCode.VALUE_HAS_TRAILING_SPACE, key, lineno,
                                    "Value has trailing whitespace"))

        if key in seen_keys:
            issues.append(LintIssue(LintCode.DUPLICATE_KEY, key, lineno,
                                    f"Duplicate of line {seen_keys[key]}"))
        else:
            seen_keys[key] = lineno

        if dominant_quote and value.startswith(("'", '"')):
            if not value.startswith(dominant_quote):
                issues.append(LintIssue(LintCode.INCONSISTENT_QUOTE_STYLE, key, lineno,
                                        f"Expected {dominant_quote!r} quotes"))

    return LintReport(issues=issues)
