"""Promote .env values from one environment to another with optional key filtering."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Set

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class PromoteResult:
    source_env: str
    target_env: str
    promoted: List[EnvEntry] = field(default_factory=list)
    skipped: List[EnvEntry] = field(default_factory=list)
    overwritten: List[EnvEntry] = field(default_factory=list)

    def promoted_count(self) -> int:
        return len(self.promoted)

    def skipped_count(self) -> int:
        return len(self.skipped)

    def overwritten_count(self) -> int:
        return len(self.overwritten)

    def summary(self) -> str:
        return (
            f"Promoted {self.promoted_count()} key(s) from '{self.source_env}' "
            f"to '{self.target_env}' "
            f"({self.overwritten_count()} overwritten, {self.skipped_count()} skipped)."
        )

    def as_envfile(self) -> EnvFile:
        """Return an EnvFile containing only the promoted entries."""
        return EnvFile(entries=list(self.promoted))


def promote_env(
    source: EnvFile,
    target: EnvFile,
    source_env: str = "source",
    target_env: str = "target",
    keys: Optional[List[str]] = None,
    overwrite: bool = True,
) -> PromoteResult:
    """Promote entries from *source* into *target*.

    Args:
        source: The environment to promote values from.
        target: The environment to promote values into.
        source_env: Human-readable label for the source environment.
        target_env: Human-readable label for the target environment.
        keys: Optional allowlist of key names to promote. Promotes all if None.
        overwrite: When True, existing keys in *target* are overwritten.

    Returns:
        A :class:`PromoteResult` describing what changed.
    """
    result = PromoteResult(source_env=source_env, target_env=target_env)

    target_keys: Set[str] = {
        e.key for e in target.entries if e.key is not None
    }
    allowlist: Optional[Set[str]] = set(keys) if keys else None

    for entry in source.entries:
        if entry.key is None:
            # comment or blank line — skip
            continue
        if allowlist is not None and entry.key not in allowlist:
            result.skipped.append(entry)
            continue
        if entry.key in target_keys and not overwrite:
            result.skipped.append(entry)
            continue
        if entry.key in target_keys:
            result.overwritten.append(entry)
        result.promoted.append(entry)

    return result
