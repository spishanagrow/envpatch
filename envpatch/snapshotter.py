"""Snapshot support: capture and compare .env file states over time."""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from envpatch.parser import EnvFile, as_dict
from envpatch.redactor import redact_file


@dataclass
class Snapshot:
    """An immutable record of an EnvFile state at a point in time."""
    label: str
    timestamp: str
    checksum: str
    entries: Dict[str, str]  # redacted values

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "timestamp": self.timestamp,
            "checksum": self.checksum,
            "entries": self.entries,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            label=data["label"],
            timestamp=data["timestamp"],
            checksum=data["checksum"],
            entries=data["entries"],
        )

    @classmethod
    def from_json(cls, raw: str) -> "Snapshot":
        return cls.from_dict(json.loads(raw))


def _checksum(env_file: EnvFile) -> str:
    """Return a stable SHA-256 hex digest of the env file's key=value content."""
    pairs = sorted(f"{e.key}={e.value}" for e in env_file.entries)
    content = "\n".join(pairs).encode()
    return hashlib.sha256(content).hexdigest()


def take_snapshot(env_file: EnvFile, label: str, mask: str = "***") -> Snapshot:
    """Capture a redacted snapshot of *env_file* tagged with *label*."""
    redacted = redact_file(env_file, mask=mask)
    return Snapshot(
        label=label,
        timestamp=datetime.now(timezone.utc).isoformat(),
        checksum=_checksum(env_file),
        entries=as_dict(redacted),
    )


def snapshots_differ(a: Snapshot, b: Snapshot) -> bool:
    """Return True when two snapshots have different checksums."""
    return a.checksum != b.checksum


def changed_keys(a: Snapshot, b: Snapshot) -> Dict[str, tuple]:
    """Return a mapping of key -> (old_value, new_value) for every changed key."""
    all_keys = set(a.entries) | set(b.entries)
    return {
        k: (a.entries.get(k), b.entries.get(k))
        for k in all_keys
        if a.entries.get(k) != b.entries.get(k)
    }
