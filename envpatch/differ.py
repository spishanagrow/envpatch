"""Diff two EnvFile objects and produce a structured diff result."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from envpatch.parser import EnvFile, as_dict


class ChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


@dataclass
class DiffEntry:
    key: str
    change_type: ChangeType
    old_value: Optional[str] = None
    new_value: Optional[str] = None

    def is_secret(self) -> bool:
        """Heuristic: treat keys containing SECRET, KEY, TOKEN, PASS as sensitive."""
        upper = self.key.upper()
        return any(word in upper for word in ("SECRET", "KEY", "TOKEN", "PASS", "PWD", "CREDENTIAL"))

    def masked_old(self) -> Optional[str]:
        return "***" if self.is_secret() and self.old_value is not None else self.old_value

    def masked_new(self) -> Optional[str]:
        return "***" if self.is_secret() and self.new_value is not None else self.new_value


@dataclass
class DiffResult:
    entries: List[DiffEntry] = field(default_factory=list)

    def added(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.change_type == ChangeType.ADDED]

    def removed(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.change_type == ChangeType.REMOVED]

    def modified(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.change_type == ChangeType.MODIFIED]

    def has_changes(self) -> bool:
        return any(e.change_type != ChangeType.UNCHANGED for e in self.entries)

    def summary(self) -> str:
        """Return a human-readable one-line summary of the diff result."""
        added = len(self.added())
        removed = len(self.removed())
        modified = len(self.modified())
        parts = []
        if added:
            parts.append(f"{added} added")
        if removed:
            parts.append(f"{removed} removed")
        if modified:
            parts.append(f"{modified} modified")
        return ", ".join(parts) if parts else "no changes"


def diff_env_files(base: EnvFile, target: EnvFile, include_unchanged: bool = False) -> DiffResult:
    """Compare base and target EnvFile objects and return a DiffResult."""
    base_dict: Dict[str, str] = as_dict(base)
    target_dict: Dict[str, str] = as_dict(target)

    all_keys = sorted(set(base_dict) | set(target_dict))
    entries: List[DiffEntry] = []

    for key in all_keys:
        in_base = key in base_dict
        in_target = key in target_dict

        if in_base and in_target:
            if base_dict[key] == target_dict[key]:
                if include_unchanged:
                    entries.append(DiffEntry(key, ChangeType.UNCHANGED, base_dict[key], target_dict[key]))
            else:
                entries.append(DiffEntry(key, ChangeType.MODIFIED, base_dict[key], target_dict[key]))
        elif in_target:
            entries.append(DiffEntry(key, ChangeType.ADDED, None, target_dict[key]))
        else:
            entries.append(DiffEntry(key, ChangeType.REMOVED, base_dict[key], None))

    return DiffResult(entries=entries)
