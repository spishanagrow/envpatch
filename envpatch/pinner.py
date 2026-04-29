"""Pin specific keys in an .env file so they are protected from merges and patches."""

from dataclasses import dataclass, field
from typing import FrozenSet, List

from envpatch.parser import EnvFile, EnvEntry


@dataclass
class PinResult:
    pinned: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    file: EnvFile = field(default_factory=lambda: EnvFile(entries=[]))

    def pinned_count(self) -> int:
        return len(self.pinned)

    def skipped_count(self) -> int:
        return len(self.skipped)

    def summary(self) -> str:
        return (
            f"Pinned {self.pinned_count()} key(s), "
            f"skipped {self.skipped_count()} unknown key(s)."
        )


def _mark_pinned(entry: EnvEntry, pin_comment: str = "# pinned") -> EnvEntry:
    """Return a copy of the entry with a pinned marker in its comment."""
    existing = entry.comment or ""
    new_comment = f"{existing} {pin_comment}".strip() if existing else pin_comment
    return EnvEntry(
        key=entry.key,
        value=entry.value,
        comment=new_comment,
        line_number=entry.line_number,
    )


def is_pinned(entry: EnvEntry, pin_comment: str = "# pinned") -> bool:
    """Return True if the entry carries the pinned marker."""
    return pin_comment in (entry.comment or "")


def pin_keys(env_file: EnvFile, keys: List[str]) -> PinResult:
    """Mark the given keys as pinned inside *env_file*.

    Keys that do not exist in the file are recorded as skipped.
    """
    existing_keys: FrozenSet[str] = frozenset(
        e.key for e in env_file.entries if e.key is not None
    )
    result = PinResult()

    key_set = set(keys)
    updated_entries: List[EnvEntry] = []

    for entry in env_file.entries:
        if entry.key in key_set:
            updated_entries.append(_mark_pinned(entry))
            result.pinned.append(entry.key)
        else:
            updated_entries.append(entry)

    for key in keys:
        if key not in existing_keys:
            result.skipped.append(key)

    result.file = EnvFile(entries=updated_entries)
    return result
