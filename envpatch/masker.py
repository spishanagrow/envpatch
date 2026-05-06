"""masker.py — selectively mask values in an EnvFile for safe display or export."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Set

from envpatch.parser import EnvEntry, EnvFile
from envpatch.differ import is_secret

DEFAULT_MASK = "***"


@dataclass
class MaskResult:
    entries: List[EnvEntry]
    masked_keys: List[str] = field(default_factory=list)
    plain_keys: List[str] = field(default_factory=list)

    def as_envfile(self) -> EnvFile:
        return EnvFile(entries=self.entries)

    def masked_count(self) -> int:
        return len(self.masked_keys)

    def plain_count(self) -> int:
        return len(self.plain_keys)

    def summary(self) -> str:
        return (
            f"{self.masked_count()} key(s) masked, "
            f"{self.plain_count()} key(s) left plain."
        )


def _mask_entry(entry: EnvEntry, mask: str) -> EnvEntry:
    """Return a copy of *entry* with its value replaced by *mask*."""
    return EnvEntry(
        key=entry.key,
        value=mask,
        comment=entry.comment,
        line_number=entry.line_number,
    )


def mask_file(
    env_file: EnvFile,
    *,
    keys: Optional[Set[str]] = None,
    secrets_only: bool = True,
    mask: str = DEFAULT_MASK,
) -> MaskResult:
    """Mask values in *env_file*.

    Parameters
    ----------
    env_file:
        The parsed env file to process.
    keys:
        Explicit set of key names to mask.  When provided, *secrets_only* is
        ignored for keys not in this set.
    secrets_only:
        When *True* (default) and *keys* is *None*, only entries whose key
        names look like secrets (via :func:`is_secret`) are masked.
    mask:
        The replacement string used as the masked value.
    """
    result_entries: List[EnvEntry] = []
    masked_keys: List[str] = []
    plain_keys: List[str] = []

    for entry in env_file.entries:
        if entry.key is None:
            # Blank lines / comment-only lines — pass through unchanged.
            result_entries.append(entry)
            continue

        should_mask = False
        if keys is not None:
            should_mask = entry.key in keys
        elif secrets_only:
            should_mask = is_secret(entry.key)

        if should_mask:
            result_entries.append(_mask_entry(entry, mask))
            masked_keys.append(entry.key)
        else:
            result_entries.append(entry)
            plain_keys.append(entry.key)

    return MaskResult(
        entries=result_entries,
        masked_keys=masked_keys,
        plain_keys=plain_keys,
    )
