"""Group env file entries by prefix or explicit tag map."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class GroupResult:
    groups: Dict[str, List[EnvEntry]] = field(default_factory=dict)
    ungrouped: List[EnvEntry] = field(default_factory=list)

    def group_names(self) -> List[str]:
        return sorted(self.groups.keys())

    def entries_for(self, group: str) -> List[EnvEntry]:
        return self.groups.get(group, [])

    def total_grouped(self) -> int:
        return sum(len(v) for v in self.groups.values())

    def summary(self) -> str:
        parts = [f"{name}({len(entries)})" for name, entries in sorted(self.groups.items())]
        ungrouped = len(self.ungrouped)
        base = ", ".join(parts) if parts else "(none)"
        return f"Groups: {base}; ungrouped: {ungrouped}"


def _prefix_of(key: str, sep: str = "_") -> Optional[str]:
    """Return the first segment of a key split by *sep*, or None if no sep."""
    if sep in key:
        return key.split(sep, 1)[0]
    return None


def group_by_prefix(
    env_file: EnvFile,
    sep: str = "_",
    min_group_size: int = 1,
) -> GroupResult:
    """Auto-group entries by key prefix (e.g. DB_HOST → group 'DB')."""
    buckets: Dict[str, List[EnvEntry]] = {}
    ungrouped: List[EnvEntry] = []

    for entry in env_file.entries:
        prefix = _prefix_of(entry.key, sep)
        if prefix:
            buckets.setdefault(prefix, []).append(entry)
        else:
            ungrouped.append(entry)

    # Demote small groups to ungrouped
    groups: Dict[str, List[EnvEntry]] = {}
    for name, members in buckets.items():
        if len(members) >= min_group_size:
            groups[name] = members
        else:
            ungrouped.extend(members)

    return GroupResult(groups=groups, ungrouped=ungrouped)


def group_by_map(
    env_file: EnvFile,
    group_map: Dict[str, List[str]],
) -> GroupResult:
    """Group entries according to an explicit {group_name: [key, ...]} map."""
    assigned: Dict[str, str] = {}
    for group_name, keys in group_map.items():
        for k in keys:
            assigned[k] = group_name

    groups: Dict[str, List[EnvEntry]] = {}
    ungrouped: List[EnvEntry] = []

    for entry in env_file.entries:
        group_name = assigned.get(entry.key)
        if group_name:
            groups.setdefault(group_name, []).append(entry)
        else:
            ungrouped.append(entry)

    return GroupResult(groups=groups, ungrouped=ungrouped)
