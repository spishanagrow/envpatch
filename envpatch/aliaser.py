"""aliaser.py — map env keys to human-friendly aliases and resolve them back."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class AliasResult:
    """Result of applying an alias map to an EnvFile."""
    entries: List[EnvEntry]
    alias_map: Dict[str, str]          # alias -> original key
    resolved: Dict[str, str]           # alias -> value
    unresolved: List[str]              # aliases with no matching key

    def keys_for_alias(self, alias: str) -> Optional[str]:
        """Return the original key name for *alias*, or None."""
        return self.alias_map.get(alias)

    def value_for_alias(self, alias: str) -> Optional[str]:
        """Return the resolved value for *alias*, or None."""
        return self.resolved.get(alias)

    def summary(self) -> str:
        total = len(self.alias_map)
        ok = len(self.resolved)
        bad = len(self.unresolved)
        return (
            f"{ok}/{total} aliases resolved"
            + (f", {bad} unresolved: {', '.join(self.unresolved)}" if bad else "")
        )


def alias_file(
    env: EnvFile,
    alias_map: Dict[str, str],
) -> AliasResult:
    """Resolve *alias_map* (alias -> original_key) against *env*.

    Parameters
    ----------
    env:
        Parsed environment file.
    alias_map:
        Mapping of human-friendly alias names to the real key names they
        stand for (e.g. ``{"db_pass": "DATABASE_PASSWORD"}``).

    Returns
    -------
    AliasResult
        Contains every alias with its resolved value (if found) and a list
        of aliases that could not be resolved.
    """
    kv: Dict[str, str] = {e.key: e.value for e in env.entries if e.key}
    resolved: Dict[str, str] = {}
    unresolved: List[str] = []

    for alias, original in alias_map.items():
        if original in kv:
            resolved[alias] = kv[original]
        else:
            unresolved.append(alias)

    return AliasResult(
        entries=list(env.entries),
        alias_map=dict(alias_map),
        resolved=resolved,
        unresolved=unresolved,
    )


def reverse_alias_map(alias_map: Dict[str, str]) -> Dict[str, List[str]]:
    """Invert *alias_map* so each original key maps to its list of aliases."""
    rev: Dict[str, List[str]] = {}
    for alias, original in alias_map.items():
        rev.setdefault(original, []).append(alias)
    return rev
