"""Normalize .env file keys and values to a consistent format."""

from dataclasses import dataclass, field
from typing import List, Optional

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class NormalizeResult:
    entries: List[EnvEntry]
    normalized_keys: List[str] = field(default_factory=list)
    normalized_values: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    def normalized_count(self) -> int:
        return len(set(self.normalized_keys + self.normalized_values))

    def skipped_count(self) -> int:
        return len(self.skipped)

    def as_envfile(self) -> EnvFile:
        return EnvFile(entries=self.entries)

    def summary(self) -> str:
        parts = []
        if self.normalized_keys:
            parts.append(f"{len(self.normalized_keys)} key(s) uppercased")
        if self.normalized_values:
            parts.append(f"{len(self.normalized_values)} value(s) stripped")
        if self.skipped:
            parts.append(f"{self.skipped_count()} skipped")
        return ", ".join(parts) if parts else "nothing to normalize"


def _normalize_key(key: str) -> str:
    return key.strip().upper()


def _normalize_value(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return value.strip()


def normalize_file(
    env_file: EnvFile,
    uppercase_keys: bool = True,
    strip_values: bool = True,
) -> NormalizeResult:
    """Return a new EnvFile with keys uppercased and/or values stripped."""
    normalized_keys: List[str] = []
    normalized_values: List[str] = []
    skipped: List[str] = []
    new_entries: List[EnvEntry] = []

    for entry in env_file.entries:
        if entry.key is None:
            # comment or blank line — pass through unchanged
            new_entries.append(entry)
            continue

        new_key = _normalize_key(entry.key) if uppercase_keys else entry.key
        new_value = _normalize_value(entry.value) if strip_values else entry.value

        key_changed = new_key != entry.key
        value_changed = new_value != entry.value

        if key_changed:
            normalized_keys.append(new_key)
        if value_changed:
            normalized_values.append(new_key)
        if not key_changed and not value_changed:
            skipped.append(entry.key)

        new_entries.append(
            EnvEntry(
                key=new_key,
                value=new_value,
                comment=entry.comment,
                line_number=entry.line_number,
                raw=entry.raw,
            )
        )

    return NormalizeResult(
        entries=new_entries,
        normalized_keys=normalized_keys,
        normalized_values=normalized_values,
        skipped=skipped,
    )
