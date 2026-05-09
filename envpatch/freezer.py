"""freezer.py — freeze an EnvFile so that pinned keys cannot be modified."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envpatch.parser import EnvEntry, EnvFile

_FREEZE_MARKER = "envpatch:frozen"


@dataclass
class FreezeResult:
    frozen: List[EnvEntry] = field(default_factory=list)
    already_frozen: List[EnvEntry] = field(default_factory=list)
    skipped: List[EnvEntry] = field(default_factory=list)
    entries: List[EnvEntry] = field(default_factory=list)

    @property
    def frozen_count(self) -> int:
        return len(self.frozen)

    @property
    def already_frozen_count(self) -> int:
        return len(self.already_frozen)

    def as_envfile(self) -> EnvFile:
        return EnvFile(entries=self.entries)

    def summary(self) -> str:
        return (
            f"frozen={self.frozen_count} "
            f"already_frozen={self.already_frozen_count} "
            f"skipped={len(self.skipped)}"
        )


def is_frozen(entry: EnvEntry) -> bool:
    """Return True if the entry carries the freeze marker in its comment."""
    comment = entry.comment or ""
    return _FREEZE_MARKER in comment


def _freeze_entry(entry: EnvEntry) -> EnvEntry:
    existing = entry.comment.strip() if entry.comment else ""
    new_comment = f"{existing} {_FREEZE_MARKER}".strip() if existing else _FREEZE_MARKER
    return EnvEntry(
        key=entry.key,
        value=entry.value,
        comment=new_comment,
        line_number=entry.line_number,
        raw=entry.raw,
    )


def freeze_file(
    env_file: EnvFile,
    keys: Optional[List[str]] = None,
) -> FreezeResult:
    """Mark entries as frozen.  If *keys* is given only those keys are frozen."""
    result = FreezeResult()
    for entry in env_file.entries:
        if entry.key is None:
            result.entries.append(entry)
            continue
        if keys is not None and entry.key not in keys:
            result.skipped.append(entry)
            result.entries.append(entry)
            continue
        if is_frozen(entry):
            result.already_frozen.append(entry)
            result.entries.append(entry)
        else:
            frozen = _freeze_entry(entry)
            result.frozen.append(frozen)
            result.entries.append(frozen)
    return result
