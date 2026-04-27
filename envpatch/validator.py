"""Validate .env files for common issues and policy violations."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List

from envpatch.parser import EnvFile


class Severity(str, Enum):
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationIssue:
    key: str
    message: str
    severity: Severity
    line_number: int = 0

    def __str__(self) -> str:
        loc = f" (line {self.line_number})" if self.line_number else ""
        return f"[{self.severity.upper()}] {self.key}{loc}: {self.message}"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == Severity.ERROR for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == Severity.WARNING for i in self.issues)

    @property
    def is_valid(self) -> bool:
        return not self.has_errors


# Keys that must never have empty values in a valid env file
_REQUIRED_NON_EMPTY = {"DATABASE_URL", "SECRET_KEY", "API_KEY"}

# Patterns that suggest a placeholder / unset secret
_PLACEHOLDER_PATTERNS = ("changeme", "replace_me", "your_", "<", "todo", "fixme")


def validate_env_file(env_file: EnvFile) -> ValidationResult:
    """Run all validation checks on an EnvFile and return a ValidationResult."""
    result = ValidationResult()

    for entry in env_file.entries:
        key = entry.key
        value = entry.value
        lineno = entry.line_number

        # Check for empty values on known critical keys
        if key in _REQUIRED_NON_EMPTY and not value:
            result.issues.append(ValidationIssue(
                key=key,
                message="required key must not be empty",
                severity=Severity.ERROR,
                line_number=lineno,
            ))

        # Check for placeholder values
        lower_val = value.lower()
        for pattern in _PLACEHOLDER_PATTERNS:
            if pattern in lower_val:
                result.issues.append(ValidationIssue(
                    key=key,
                    message=f"value looks like a placeholder (contains '{pattern}')",
                    severity=Severity.WARNING,
                    line_number=lineno,
                ))
                break

        # Check for keys with no value at all (not just empty string)
        if value == "" and key not in _REQUIRED_NON_EMPTY:
            result.issues.append(ValidationIssue(
                key=key,
                message="key has an empty value",
                severity=Severity.WARNING,
                line_number=lineno,
            ))

    return result
