"""Sort .env file entries by key name, prefix group, or custom order."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class SortResult:
    original: EnvFile
    sorted_entries: List[EnvEntry]
    moved_count: int

    def as_envfile(self) -> EnvFile:
        return EnvFile(entries=self.sorted_entries)

    def as_string(self) -> str:
        lines: List[str] = []
        for entry in self.sorted_entries:
            if entry.comment is not None:
                lines.append(entry.comment)
            if entry.key is not None:
                value = entry.raw_value if entry.raw_value is not None else entry.value
                lines.append(f"{entry.key}={value}")
        return "\n".join(lines)

    def summary(self) -> str:
        if self.moved_count == 0:
            return "Already sorted — no changes made."
        return f"Sorted {self.moved_count} key(s) into new positions."


def _key_func_alpha(entry: EnvEntry) -> str:
    return (entry.key or "").lower()


def _key_func_prefix(entry: EnvEntry) -> tuple:
    key = entry.key or ""
    parts = key.split("_", 1)
    prefix = parts[0].lower() if len(parts) > 1 else ""
    return (prefix, key.lower())


def sort_file(
    env_file: EnvFile,
    mode: str = "alpha",
    key_func: Optional[Callable[[EnvEntry], object]] = None,
    reverse: bool = False,
) -> SortResult:
    """Sort entries in *env_file*.

    Parameters
    ----------
    env_file:
        Parsed .env file to sort.
    mode:
        ``"alpha"`` (default) — alphabetical by key name.
        ``"prefix"`` — group by underscore prefix then alphabetical.
    key_func:
        Optional custom sort key callable; overrides *mode*.
    reverse:
        If ``True``, sort in descending order.
    """
    real_entries = [e for e in env_file.entries if e.key is not None]
    comment_entries = [e for e in env_file.entries if e.key is None]

    sorter = key_func or (_key_func_prefix if mode == "prefix" else _key_func_alpha)
    sorted_real = sorted(real_entries, key=sorter, reverse=reverse)

    original_keys = [e.key for e in real_entries]
    sorted_keys = [e.key for e in sorted_real]
    moved = sum(1 for a, b in zip(original_keys, sorted_keys) if a != b)

    final_entries = comment_entries + sorted_real

    return SortResult(
        original=env_file,
        sorted_entries=final_entries,
        moved_count=moved,
    )
