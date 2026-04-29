"""Build and query a timeline of snapshots for an env file."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List, Optional

from envpatch.snapshotter import Snapshot, to_dict as snap_to_dict, from_dict as snap_from_dict
from envpatch.comparator import compare_snapshots, SnapshotDiff


@dataclass
class Timeline:
    """Ordered collection of snapshots representing env file history."""

    name: str
    snapshots: List[Snapshot] = field(default_factory=list)

    def record(self, snapshot: Snapshot) -> None:
        """Append a snapshot to the timeline."""
        self.snapshots.append(snapshot)

    @property
    def latest(self) -> Optional[Snapshot]:
        return self.snapshots[-1] if self.snapshots else None

    @property
    def earliest(self) -> Optional[Snapshot]:
        return self.snapshots[0] if self.snapshots else None

    def at(self, index: int) -> Snapshot:
        return self.snapshots[index]

    def diff_adjacent(self, index: int) -> SnapshotDiff:
        """Compare snapshot at index-1 with snapshot at index."""
        if index < 1 or index >= len(self.snapshots):
            raise IndexError(f"No adjacent pair at index {index}")
        return compare_snapshots(self.snapshots[index - 1], self.snapshots[index])

    def diff_range(self, start: int, end: int) -> SnapshotDiff:
        """Compare snapshot at start with snapshot at end."""
        return compare_snapshots(self.snapshots[start], self.snapshots[end])

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "snapshots": [snap_to_dict(s) for s in self.snapshots],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> "Timeline": 
        tl = cls(name=data["name"])
        tl.snapshots = [snap_from_dict(s) for s in data.get("snapshots", [])]
        return tl

    @classmethod
    def from_json(cls, raw: str) -> "Timeline":
        return cls.from_dict(json.loads(raw))
