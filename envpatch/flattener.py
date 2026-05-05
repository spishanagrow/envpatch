"""Flatten nested or prefixed .env keys into a structured dict, or expand a dict back to flat env entries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class FlattenResult:
    nested: Dict[str, object]
    entries: List[EnvEntry]
    separator: str

    def keys(self) -> List[str]:
        return [e.key for e in self.entries]

    def summary(self) -> str:
        top = len(self.nested)
        total = len(self.entries)
        return f"Flattened {total} entries into {top} top-level group(s) using '{self.separator}'"


def _insert(target: dict, parts: List[str], value: str) -> None:
    """Recursively insert a value into a nested dict following key parts."""
    for part in parts[:-1]:
        target = target.setdefault(part, {})
    leaf = parts[-1]
    if leaf in target and isinstance(target[leaf], dict):
        target[leaf]["__value__"] = value
    else:
        target[leaf] = value


def flatten_file(env_file: EnvFile, separator: str = "__") -> FlattenResult:
    """Convert a flat EnvFile into a nested dict by splitting keys on *separator*.

    Keys that do not contain the separator are placed at the top level.
    The original EnvEntry list is preserved unchanged.
    """
    nested: Dict[str, object] = {}
    entries: List[EnvEntry] = []

    for entry in env_file.entries:
        if entry.key is None:
            continue
        parts = entry.key.split(separator) if separator in entry.key else [entry.key]
        _insert(nested, parts, entry.value or "")
        entries.append(entry)

    return FlattenResult(nested=nested, entries=entries, separator=separator)


def expand_dict(
    data: Dict[str, object],
    separator: str = "__",
    prefix: Optional[str] = None,
) -> List[EnvEntry]:
    """Recursively expand a nested dict back into a flat list of EnvEntry objects."""
    result: List[EnvEntry] = []
    for key, value in data.items():
        full_key = f"{prefix}{separator}{key}" if prefix else key
        if isinstance(value, dict):
            leaf = value.pop("__value__", None)
            if leaf is not None:
                result.append(EnvEntry(key=full_key, value=str(leaf), comment=None, line=0))
            result.extend(expand_dict(value, separator=separator, prefix=full_key))
        else:
            result.append(EnvEntry(key=full_key, value=str(value), comment=None, line=0))
    return result
