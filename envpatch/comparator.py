"""Compare two snapshots and produce a structured change report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envpatch.snapshotter import Snapshot
from envpatch.differ import ChangeType, is_secret


@dataclass
class SnapshotDiff:
    """Result of comparing two snapshots."""

    before_label: str
    after_label: str
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)
    unchanged: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.modified)

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.removed) + len(self.modified)

    def to_dict(self) -> dict:
        return {
            "before": self.before_label,
            "after": self.after_label,
            "added": self.added,
            "removed": self.removed,
            "modified": self.modified,
            "unchanged": self.unchanged,
            "total_changes": self.total_changes,
        }


def compare_snapshots(
    before: Snapshot,
    after: Snapshot,
    before_label: Optional[str] = None,
    after_label: Optional[str] = None,
) -> SnapshotDiff:
    """Compare two snapshots and return a SnapshotDiff."""
    label_a = before_label or before.label or "before"
    label_b = after_label or after.label or "after"

    before_keys: Dict[str, str] = {e.key: e.value for e in before.entries}
    after_keys: Dict[str, str] = {e.key: e.value for e in after.entries}

    all_keys = set(before_keys) | set(after_keys)

    diff = SnapshotDiff(before_label=label_a, after_label=label_b)

    for key in sorted(all_keys):
        if key not in before_keys:
            diff.added.append(key)
        elif key not in after_keys:
            diff.removed.append(key)
        elif before_keys[key] != after_keys[key]:
            diff.modified.append(key)
        else:
            diff.unchanged.append(key)

    return diff


def format_snapshot_diff(diff: SnapshotDiff, redact: bool = True) -> str:
    """Return a human-readable summary of a SnapshotDiff."""
    lines = [
        f"Comparing '{diff.before_label}' -> '{diff.after_label}'",
        f"  + added:    {len(diff.added)}",
        f"  - removed:  {len(diff.removed)}",
        f"  ~ modified: {len(diff.modified)}",
        f"  = unchanged:{len(diff.unchanged)}",
    ]
    if diff.added:
        lines.append("Added keys:    " + ", ".join(diff.added))
    if diff.removed:
        lines.append("Removed keys:  " + ", ".join(diff.removed))
    if diff.modified:
        lines.append("Modified keys: " + ", ".join(diff.modified))
    return "\n".join(lines)
