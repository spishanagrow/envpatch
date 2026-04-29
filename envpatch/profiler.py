"""Profile an .env file and report statistics and patterns."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envpatch.parser import EnvFile
from envpatch.differ import is_secret


@dataclass
class ProfileReport:
    total_keys: int = 0
    secret_keys: int = 0
    plain_keys: int = 0
    empty_values: int = 0
    placeholder_values: int = 0
    quoted_values: int = 0
    comment_count: int = 0
    secret_names: List[str] = field(default_factory=list)
    placeholder_names: List[str] = field(default_factory=list)
    empty_names: List[str] = field(default_factory=list)

    def secret_ratio(self) -> float:
        """Fraction of keys considered secrets (0.0 – 1.0)."""
        if self.total_keys == 0:
            return 0.0
        return self.secret_keys / self.total_keys

    def to_dict(self) -> dict:
        return {
            "total_keys": self.total_keys,
            "secret_keys": self.secret_keys,
            "plain_keys": self.plain_keys,
            "empty_values": self.empty_values,
            "placeholder_values": self.placeholder_values,
            "quoted_values": self.quoted_values,
            "comment_count": self.comment_count,
            "secret_ratio": round(self.secret_ratio(), 4),
            "secret_names": self.secret_names,
            "placeholder_names": self.placeholder_names,
            "empty_names": self.empty_names,
        }


_PLACEHOLDER_PATTERNS = ("changeme", "todo", "your_", "<", ">", "example", "xxx")


def _is_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(pat in lowered for pat in _PLACEHOLDER_PATTERNS)


def profile_file(env_file: EnvFile) -> ProfileReport:
    """Analyse *env_file* and return a :class:`ProfileReport`."""
    report = ProfileReport()

    report.comment_count = sum(
        1 for line in env_file.raw_lines if line.strip().startswith("#")
    )

    for entry in env_file.entries:
        report.total_keys += 1

        if is_secret(entry.key):
            report.secret_keys += 1
            report.secret_names.append(entry.key)
        else:
            report.plain_keys += 1

        if entry.value == "":
            report.empty_values += 1
            report.empty_names.append(entry.key)
        elif _is_placeholder(entry.value):
            report.placeholder_values += 1
            report.placeholder_names.append(entry.key)

        if entry.raw_value and (
            entry.raw_value.startswith('"') or entry.raw_value.startswith("'")
        ):
            report.quoted_values += 1

    return report
