"""Detect and remove duplicate keys from an .env file."""

from dataclasses import dataclass, field
from typing import List, Dict

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class DeduplicateResult:
    entries: List[EnvEntry]
    duplicates: Dict[str, List[int]]  # key -> list of line numbers where duplicates appeared
    kept: Dict[str, int]             # key -> line number of the entry that was kept


def duplicate_keys(env_file: EnvFile) -> Dict[str, List[int]]:
    """Return a mapping of key -> line numbers for every key that appears more than once."""
    seen: Dict[str, List[int]] = {}
    for entry in env_file.entries:
        if entry.key is None:
            continue
        seen.setdefault(entry.key, []).append(entry.line_number)
    return {k: lines for k, lines in seen.items() if len(lines) > 1}


def has_duplicates(env_file: EnvFile) -> bool:
    """Return True if the file contains any duplicate keys."""
    return bool(duplicate_keys(env_file))


def deduplicate(
    env_file: EnvFile,
    keep: str = "last",
) -> DeduplicateResult:
    """Remove duplicate keys, keeping either the 'first' or 'last' occurrence.

    Non-key lines (blank lines, comments) are always preserved.
    """
    if keep not in ("first", "last"):
        raise ValueError("keep must be 'first' or 'last'")

    dupes = duplicate_keys(env_file)

    # Determine which line number to keep for each duplicated key
    kept: Dict[str, int] = {}
    for key, lines in dupes.items():
        kept[key] = lines[0] if keep == "first" else lines[-1]

    result_entries: List[EnvEntry] = []
    for entry in env_file.entries:
        if entry.key is None or entry.key not in dupes:
            result_entries.append(entry)
        elif entry.line_number == kept[entry.key]:
            result_entries.append(entry)
        # else: skip — it's a duplicate we're dropping

    return DeduplicateResult(
        entries=result_entries,
        duplicates=dupes,
        kept=kept,
    )


def as_envfile(result: DeduplicateResult) -> str:
    """Render deduplicated entries back to .env string format."""
    lines = []
    for entry in result.entries:
        if entry.key is None:
            lines.append(entry.raw)
        else:
            lines.append(entry.raw)
    return "\n".join(lines)


def summary(result: DeduplicateResult) -> str:
    """Return a human-readable summary of the deduplication."""
    if not result.duplicates:
        return "No duplicate keys found."
    total = sum(len(v) - 1 for v in result.duplicates.values())
    keys = ", ".join(sorted(result.duplicates))
    return f"Removed {total} duplicate(s) across {len(result.duplicates)} key(s): {keys}"
