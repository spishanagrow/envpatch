"""Strip keys from an EnvFile by name, pattern, or tag prefix."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class StripResult:
    original: EnvFile
    stripped: EnvFile
    removed_keys: List[str] = field(default_factory=list)
    skipped_keys: List[str] = field(default_factory=list)

    def removed_count(self) -> int:
        return len(self.removed_keys)

    def skipped_count(self) -> int:
        return len(self.skipped_keys)

    def summary(self) -> str:
        return (
            f"Stripped {self.removed_count()} key(s), "
            f"skipped {self.skipped_count()} key(s)."
        )

    def as_envfile(self) -> EnvFile:
        return self.stripped


def _matches(key: str, names: List[str], pattern: Optional[str], prefix: Optional[str]) -> bool:
    if key in names:
        return True
    if prefix and key.startswith(prefix):
        return True
    if pattern:
        try:
            if re.search(pattern, key):
                return True
        except re.error:
            pass
    return False


def strip_keys(
    env_file: EnvFile,
    keys: Optional[List[str]] = None,
    pattern: Optional[str] = None,
    prefix: Optional[str] = None,
) -> StripResult:
    """Return a new EnvFile with matching keys removed.

    Args:
        env_file: Source file to strip from.
        keys: Exact key names to remove.
        pattern: Regex pattern; any matching key is removed.
        prefix: Key prefix; any key starting with this is removed.

    Returns:
        StripResult containing the cleaned file and removal metadata.
    """
    names: List[str] = keys or []
    kept: List[EnvEntry] = []
    removed: List[str] = []
    skipped: List[str] = []

    for entry in env_file.entries:
        if entry.key is None:
            # Comment or blank line — always keep
            kept.append(entry)
            continue
        if _matches(entry.key, names, pattern, prefix):
            removed.append(entry.key)
        else:
            kept.append(entry)
            skipped.append(entry.key)

    result_file = EnvFile(entries=kept, path=env_file.path)
    return StripResult(
        original=env_file,
        stripped=result_file,
        removed_keys=removed,
        skipped_keys=skipped,
    )
