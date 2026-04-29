"""Rename keys across an EnvFile, preserving order, comments, and line metadata."""

from dataclasses import dataclass, field
from typing import Dict, List

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class RenameResult:
    entries: List[EnvEntry] = field(default_factory=list)
    renamed: Dict[str, str] = field(default_factory=dict)   # old_key -> new_key
    skipped: Dict[str, str] = field(default_factory=dict)   # old_key -> reason

    def as_envfile(self, original: EnvFile) -> EnvFile:
        return EnvFile(path=original.path, entries=self.entries)


def _renamed_entry(entry: EnvEntry, new_key: str) -> EnvEntry:
    return EnvEntry(
        key=new_key,
        value=entry.value,
        raw_line=entry.raw_line,
        line_number=entry.line_number,
        comment=entry.comment,
        is_quoted=entry.is_quoted,
    )


def rename_keys(env_file: EnvFile, rename_map: Dict[str, str]) -> RenameResult:
    """Apply *rename_map* (old_key -> new_key) to *env_file*.

    Rules:
    - If old_key is not present the entry is added to ``skipped``.
    - If new_key already exists in the file the rename is skipped to avoid
      duplicate keys.
    - All other entries are carried over unchanged.
    """
    result = RenameResult()
    existing_keys = {e.key for e in env_file.entries}

    # Pre-validate: detect target collisions
    blocked: Dict[str, str] = {}
    for old_key, new_key in rename_map.items():
        if old_key not in existing_keys:
            result.skipped[old_key] = "key not found"
        elif new_key in existing_keys and new_key != old_key:
            blocked[old_key] = new_key
            result.skipped[old_key] = f"target key '{new_key}' already exists"

    for entry in env_file.entries:
        new_key = rename_map.get(entry.key)
        if new_key is None or entry.key in result.skipped:
            result.entries.append(entry)
        else:
            result.entries.append(_renamed_entry(entry, new_key))
            result.renamed[entry.key] = new_key

    return result


def summary(result: RenameResult) -> str:
    lines = []
    if result.renamed:
        for old, new in result.renamed.items():
            lines.append(f"  renamed : {old} -> {new}")
    if result.skipped:
        for key, reason in result.skipped.items():
            lines.append(f"  skipped : {key} ({reason})")
    if not lines:
        return "No renames applied."
    return "\n".join(lines)
