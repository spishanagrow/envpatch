"""Audit log for tracking env file operations (diff, merge, validate)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


class AuditAction(str, Enum):
    DIFF = "diff"
    MERGE = "merge"
    VALIDATE = "validate"
    REDACT = "redact"


@dataclass
class AuditEntry:
    action: AuditAction
    source_file: str
    target_file: Optional[str]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    user: str = field(default_factory=lambda: os.environ.get("USER", "unknown"))
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["action"] = self.action.value
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class AuditLog:
    entries: List[AuditEntry] = field(default_factory=list)

    def record(self, entry: AuditEntry) -> None:
        self.entries.append(entry)

    def to_json(self) -> str:
        return json.dumps([e.to_dict() for e in self.entries], indent=2)

    def filter_by_action(self, action: AuditAction) -> List[AuditEntry]:
        return [e for e in self.entries if e.action == action]

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.to_json())

    @classmethod
    def load(cls, path: str) -> "AuditLog":
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        log = cls()
        for item in raw:
            item["action"] = AuditAction(item["action"])
            log.entries.append(AuditEntry(**item))
        return log


def make_entry(
    action: AuditAction,
    source_file: str,
    target_file: Optional[str] = None,
    **details,
) -> AuditEntry:
    """Convenience factory for creating an AuditEntry."""
    return AuditEntry(
        action=action,
        source_file=source_file,
        target_file=target_file,
        details=details,
    )
