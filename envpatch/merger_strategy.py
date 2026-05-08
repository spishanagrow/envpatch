"""Strategy-based merge policies for resolving key conflicts."""
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

from envpatch.parser import EnvEntry, EnvFile


class MergeStrategy(str, Enum):
    OURS = "ours"       # keep base value on conflict
    THEIRS = "theirs"   # take patch value on conflict
    NEWER = "newer"     # prefer entry with higher line number (patch wins ties)
    ASK = "ask"         # reserved; callers must resolve externally


@dataclass
class StrategyResult:
    entries: list
    resolved: list = field(default_factory=list)   # keys resolved by strategy
    kept: list = field(default_factory=list)        # keys where base won
    overwritten: list = field(default_factory=list) # keys where patch won

    def summary(self) -> str:
        parts = []
        if self.overwritten:
            parts.append(f"{len(self.overwritten)} overwritten")
        if self.kept:
            parts.append(f"{len(self.kept)} kept")
        if not parts:
            return "no conflicts"
        return ", ".join(parts)

    def as_envfile(self) -> EnvFile:
        return EnvFile(entries=self.entries)


def apply_strategy(
    base: EnvFile,
    patch: EnvFile,
    strategy: MergeStrategy = MergeStrategy.THEIRS,
) -> StrategyResult:
    """Merge *patch* into *base* using the given conflict-resolution strategy."""
    base_map: dict[str, EnvEntry] = {
        e.key: e for e in base.entries if e.key is not None
    }
    patch_map: dict[str, EnvEntry] = {
        e.key: e for e in patch.entries if e.key is not None
    }

    resolved: list[str] = []
    kept: list[str] = []
    overwritten: list[str] = []
    merged: list[EnvEntry] = []

    # Walk base entries preserving order
    for entry in base.entries:
        if entry.key is None:
            merged.append(entry)
            continue
        if entry.key in patch_map:
            conflict_key = entry.key
            patch_entry = patch_map[conflict_key]
            resolved.append(conflict_key)
            if strategy == MergeStrategy.OURS:
                merged.append(entry)
                kept.append(conflict_key)
            elif strategy == MergeStrategy.THEIRS:
                merged.append(patch_entry)
                overwritten.append(conflict_key)
            elif strategy == MergeStrategy.NEWER:
                if (patch_entry.line or 0) >= (entry.line or 0):
                    merged.append(patch_entry)
                    overwritten.append(conflict_key)
                else:
                    merged.append(entry)
                    kept.append(conflict_key)
            else:
                merged.append(entry)  # ASK: default to ours
                kept.append(conflict_key)
        else:
            merged.append(entry)

    # Append keys that exist only in patch
    existing_keys = {e.key for e in merged if e.key is not None}
    for entry in patch.entries:
        if entry.key is not None and entry.key not in existing_keys:
            merged.append(entry)

    return StrategyResult(
        entries=merged,
        resolved=resolved,
        kept=kept,
        overwritten=overwritten,
    )
