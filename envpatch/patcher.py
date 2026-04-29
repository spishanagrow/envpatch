"""Apply a patch (set of diff entries) to an env file, producing a new EnvFile."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envpatch.parser import EnvEntry, EnvFile
from envpatch.differ import DiffEntry, ChangeType


@dataclass
class PatchResult:
    """Outcome of applying a patch to an EnvFile."""

    file: EnvFile
    applied: List[DiffEntry] = field(default_factory=list)
    skipped: List[DiffEntry] = field(default_factory=list)

    @property
    def applied_count(self) -> int:
        return len(self.applied)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped)

    def summary(self) -> str:
        parts = []
        if self.applied:
            parts.append(f"{self.applied_count} change(s) applied")
        if self.skipped:
            parts.append(f"{self.skipped_count} change(s) skipped (key not found)")
        return ", ".join(parts) if parts else "No changes applied"


def apply_patch(
    base: EnvFile,
    patch: List[DiffEntry],
    skip_missing: bool = True,
) -> PatchResult:
    """Apply *patch* diff entries to *base*, returning a new PatchResult.

    Args:
        base: The source EnvFile to patch.
        patch: Ordered list of DiffEntry objects to apply.
        skip_missing: When True, REMOVED/MODIFIED entries whose key is absent
                      in *base* are silently skipped instead of raising.
    """
    entries: dict[str, EnvEntry] = {
        e.key: EnvEntry(e.key, e.value, e.comment, e.line_number)
        for e in base.entries
    }
    key_order: list[str] = [e.key for e in base.entries]

    applied: list[DiffEntry] = []
    skipped: list[DiffEntry] = []

    for diff in patch:
        key = diff.key

        if diff.change_type == ChangeType.ADDED:
            if key not in entries:
                entries[key] = EnvEntry(key, diff.new_value or "", None, None)
                key_order.append(key)
            else:
                entries[key] = EnvEntry(key, diff.new_value or "", entries[key].comment, entries[key].line_number)
            applied.append(diff)

        elif diff.change_type == ChangeType.MODIFIED:
            if key not in entries:
                if skip_missing:
                    skipped.append(diff)
                    continue
                raise KeyError(f"Key '{key}' not found in base file")
            entries[key] = EnvEntry(key, diff.new_value or "", entries[key].comment, entries[key].line_number)
            applied.append(diff)

        elif diff.change_type == ChangeType.REMOVED:
            if key not in entries:
                if skip_missing:
                    skipped.append(diff)
                    continue
                raise KeyError(f"Key '{key}' not found in base file")
            del entries[key]
            key_order.remove(key)
            applied.append(diff)

    new_entries = [entries[k] for k in key_order if k in entries]
    new_file = EnvFile(entries=new_entries, raw=base.raw)
    return PatchResult(file=new_file, applied=applied, skipped=skipped)
