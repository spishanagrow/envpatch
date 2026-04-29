"""Merge .env files by applying a diff patch to a base environment."""

from dataclasses import dataclass, field
from typing import List, Optional

from envpatch.differ import ChangeType, DiffEntry, diff_env_files
from envpatch.parser import EnvEntry, EnvFile


@dataclass
class MergeResult:
    """Result of merging a patch into a base .env file."""

    lines: List[str] = field(default_factory=list)
    applied: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)

    def as_string(self) -> str:
        return "\n".join(self.lines)

    @property
    def has_changes(self) -> bool:
        """Return True if any changes were successfully applied."""
        return len(self.applied) > 0

    def summary(self) -> str:
        """Return a human-readable summary of the merge result."""
        parts = [f"applied={len(self.applied)}"]
        if self.skipped:
            parts.append(f"skipped={len(self.skipped)}")
        if self.conflicts:
            parts.append(f"conflicts={len(self.conflicts)}")
        return "MergeResult(" + ", ".join(parts) + ")"


def merge_env_files(
    base: EnvFile,
    patch: EnvFile,
    skip_secrets: bool = False,
    dry_run: bool = False,
) -> MergeResult:
    """Apply patch entries onto base, returning a MergeResult.

    Args:
        base: The original EnvFile to merge into.
        patch: The target EnvFile whose changes are applied as a patch.
        skip_secrets: If True, skip keys that look like secrets.
        dry_run: If True, compute result but do not mutate anything.

    Returns:
        MergeResult with the merged lines and metadata.
    """
    from envpatch.differ import is_secret

    result = MergeResult()
    diff: List[DiffEntry] = diff_env_files(base, patch)

    # Build a mutable copy of base lines keyed by variable name
    merged: dict = {entry.key: entry.value for entry in base.entries}
    key_order: List[str] = [entry.key for entry in base.entries]
    comments_and_blanks: List[str] = [
        line for line in base.raw_lines if line.strip() == "" or line.strip().startswith("#")
    ]

    for change in diff:
        key = change.key
        if skip_secrets and is_secret(key):
            result.skipped.append(key)
            continue

        if change.change_type == ChangeType.ADDED:
            merged[key] = change.new_value
            key_order.append(key)
            result.applied.append(key)
        elif change.change_type == ChangeType.REMOVED:
            merged.pop(key, None)
            if key in key_order:
                key_order.remove(key)
            result.applied.append(key)
        elif change.change_type == ChangeType.MODIFIED:
            merged[key] = change.new_value
            result.applied.append(key)

    # Reconstruct output lines preserving order
    for key in key_order:
        if key in merged:
            value = merged[key]
            needs_quotes = " " in value or "#" in value or value == ""
            formatted = f'{key}="{value}"' if needs_quotes else f"{key}={value}"
            result.lines.append(formatted)

    return result
