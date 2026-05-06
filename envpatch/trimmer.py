"""Trim leading/trailing whitespace from env entry values."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class TrimResult:
    entries: List[EnvEntry] = field(default_factory=list)
    trimmed_keys: List[str] = field(default_factory=list)
    skipped_keys: List[str] = field(default_factory=list)

    def trimmed_count(self) -> int:
        return len(self.trimmed_keys)

    def skipped_count(self) -> int:
        return len(self.skipped_keys)

    def summary(self) -> str:
        return (
            f"Trimmed {self.trimmed_count()} key(s), "
            f"{self.skipped_count()} already clean."
        )

    def as_envfile(self) -> EnvFile:
        return EnvFile(entries=self.entries)


def _trim_entry(entry: EnvEntry) -> tuple[EnvEntry, bool]:
    """Return a (possibly new) entry with whitespace stripped from value.

    Returns the entry and a boolean indicating whether it was changed.
    """
    if entry.value is None:
        return entry, False
    stripped = entry.value.strip()
    if stripped == entry.value:
        return entry, False
    new_entry = EnvEntry(
        key=entry.key,
        value=stripped,
        comment=entry.comment,
        line_number=entry.line_number,
        raw=entry.raw,
    )
    return new_entry, True


def trim_file(
    env_file: EnvFile,
    keys: Optional[List[str]] = None,
) -> TrimResult:
    """Trim whitespace from values in *env_file*.

    If *keys* is provided only those keys are considered; otherwise every
    key-value entry is a candidate.
    """
    result = TrimResult()
    for entry in env_file.entries:
        if entry.key is None:
            # Preserve blank lines and comment-only lines unchanged.
            result.entries.append(entry)
            continue
        if keys is not None and entry.key not in keys:
            result.entries.append(entry)
            result.skipped_keys.append(entry.key)
            continue
        trimmed, changed = _trim_entry(entry)
        result.entries.append(trimmed)
        if changed:
            result.trimmed_keys.append(entry.key)
        else:
            result.skipped_keys.append(entry.key)
    return result
