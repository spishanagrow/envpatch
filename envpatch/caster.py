"""Type-casting utilities for .env values.

Provides best-effort inference and explicit casting of string values
to Python native types (bool, int, float, list).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from envpatch.parser import EnvEntry, EnvFile

_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}


def _cast_value(raw: str) -> Any:
    """Infer the most specific type for *raw*."""
    stripped = raw.strip()
    if stripped.lower() in _TRUE_VALUES:
        return True
    if stripped.lower() in _FALSE_VALUES:
        return False
    try:
        return int(stripped)
    except ValueError:
        pass
    try:
        return float(stripped)
    except ValueError:
        pass
    # Comma-separated list (at least one comma required)
    if "," in stripped:
        return [item.strip() for item in stripped.split(",")]
    return stripped


@dataclass
class CastResult:
    """Outcome of casting all entries in an EnvFile."""

    values: Dict[str, Any] = field(default_factory=dict)
    types: Dict[str, str] = field(default_factory=dict)
    cast_count: int = 0
    plain_count: int = 0

    def summary(self) -> str:
        total = self.cast_count + self.plain_count
        return (
            f"{total} key(s) processed: "
            f"{self.cast_count} cast, {self.plain_count} kept as string."
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "values": self.values,
            "types": self.types,
            "cast_count": self.cast_count,
            "plain_count": self.plain_count,
        }


def cast_file(
    env_file: EnvFile,
    keys: Optional[List[str]] = None,
) -> CastResult:
    """Cast values in *env_file*, optionally restricted to *keys*.

    Args:
        env_file: Parsed environment file.
        keys: If provided, only these keys are cast; others kept as strings.

    Returns:
        A :class:`CastResult` with typed values and metadata.
    """
    result = CastResult()
    for entry in env_file.entries:
        if entry.key is None:
            continue
        raw = entry.value or ""
        if keys is None or entry.key in keys:
            casted = _cast_value(raw)
            result.values[entry.key] = casted
            result.types[entry.key] = type(casted).__name__
            if isinstance(casted, str):
                result.plain_count += 1
            else:
                result.cast_count += 1
        else:
            result.values[entry.key] = raw
            result.types[entry.key] = "str"
            result.plain_count += 1
    return result
