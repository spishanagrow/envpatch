from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envpatch.parser import EnvEntry, EnvFile
from envpatch.differ import diff_files, ChangeType


@dataclass
class MergeResult:
    entries: List[EnvEntry]
    added: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    def as_string(self) -> str:
        return as_string(self)

    def has_changes(self) -> bool:
        return has_changes(self)

    def summary(self) -> str:
        return summary(self)


def as_string(result: MergeResult) -> str:
    lines = []
    for entry in result.entries:
        if entry.comment is not None:
            lines.append(entry.comment)
        elif entry.key is None:
            lines.append("")
        else:
            quote = '"' if entry.quoted else ""
            lines.append(f"{entry.key}={quote}{entry.value}{quote}")
    return "\n".join(lines)


def has_changes(result: MergeResult) -> bool:
    return bool(result.added or result.modified or result.removed)


def summary(result: MergeResult) -> str:
    parts = []
    if result.added:
        parts.append(f"{len(result.added)} added")
    if result.modified:
        parts.append(f"{len(result.modified)} modified")
    if result.removed:
        parts.append(f"{len(result.removed)} removed")
    if result.skipped:
        parts.append(f"{len(result.skipped)} skipped")
    if not parts:
        return "No changes."
    return ", ".join(parts) + "."


def merge_env_files(
    base: EnvFile,
    patch: EnvFile,
    keep_removed: bool = False,
    skip_keys: Optional[List[str]] = None,
) -> MergeResult:
    skip_keys = set(skip_keys or [])
    diff = diff_files(base, patch)
    patch_dict = {e.key: e for e in patch.entries if e.key is not None}
    base_entries = list(base.entries)

    result_entries: List[EnvEntry] = []
    added: List[str] = []
    modified: List[str] = []
    removed: List[str] = []
    skipped: List[str] = []

    seen_keys = set()

    for entry in base_entries:
        if entry.key is None:
            result_entries.append(entry)
            continue
        if entry.key in skip_keys:
            result_entries.append(entry)
            skipped.append(entry.key)
            seen_keys.add(entry.key)
            continue
        change = next((d for d in diff if d.key == entry.key), None)
        if change is None:
            result_entries.append(entry)
        elif change.change_type == ChangeType.MODIFIED:
            new_entry = patch_dict[entry.key]
            result_entries.append(new_entry)
            modified.append(entry.key)
        elif change.change_type == ChangeType.REMOVED:
            if keep_removed:
                result_entries.append(entry)
            else:
                removed.append(entry.key)
        else:
            result_entries.append(entry)
        seen_keys.add(entry.key)

    for diff_entry in diff:
        if diff_entry.change_type == ChangeType.ADDED and diff_entry.key not in seen_keys:
            if diff_entry.key in skip_keys:
                skipped.append(diff_entry.key)
            else:
                result_entries.append(patch_dict[diff_entry.key])
                added.append(diff_entry.key)

    return MergeResult(
        entries=result_entries,
        added=added,
        modified=modified,
        removed=removed,
        skipped=skipped,
    )
