"""Clone an EnvFile, optionally filtering to a subset of keys or scopes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Set

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class CloneResult:
    source_key: str  # original env label / filename hint
    cloned: List[EnvEntry] = field(default_factory=list)
    skipped: List[EnvEntry] = field(default_factory=list)

    @property
    def cloned_count(self) -> int:
        return len(self.cloned)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped)

    def as_envfile(self) -> EnvFile:
        return EnvFile(entries=list(self.cloned))

    def summary(self) -> str:
        return (
            f"Cloned {self.cloned_count} key(s) from '{self.source_key}'"
            f", skipped {self.skipped_count}."
        )


def clone_file(
    source: EnvFile,
    source_key: str = "source",
    keys: Optional[List[str]] = None,
    prefix: Optional[str] = None,
    exclude_secrets: bool = False,
) -> CloneResult:
    """Return a CloneResult containing entries that match the given criteria.

    Args:
        source: The EnvFile to clone from.
        source_key: A label used in the summary (e.g. filename).
        keys: If given, only entries whose key is in this list are cloned.
        prefix: If given, only entries whose key starts with this prefix are cloned.
        exclude_secrets: If True, entries detected as secrets are skipped.
    """
    from envpatch.differ import is_secret  # local import to avoid circular deps

    allowed: Optional[Set[str]] = set(keys) if keys else None
    result = CloneResult(source_key=source_key)

    for entry in source.entries:
        if entry.key is None:
            # blank lines / comments — carry them along unchanged
            result.cloned.append(entry)
            continue

        if allowed is not None and entry.key not in allowed:
            result.skipped.append(entry)
            continue

        if prefix is not None and not entry.key.startswith(prefix):
            result.skipped.append(entry)
            continue

        if exclude_secrets and is_secret(entry.key):
            result.skipped.append(entry)
            continue

        result.cloned.append(entry)

    return result
