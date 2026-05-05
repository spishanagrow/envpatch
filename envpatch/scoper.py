"""Scope filtering: restrict env entries to a named environment scope.

Entries can declare their scope via an inline comment tag, e.g.:
    DB_HOST=localhost  # scope:production
    DEBUG=true         # scope:development
Entries with no scope tag are included in every scope (universal).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envpatch.parser import EnvEntry, EnvFile

_SCOPE_RE = re.compile(r"#.*?scope:(\w+)", re.IGNORECASE)


def _entry_scope(entry: EnvEntry) -> Optional[str]:
    """Return the scope tag value from the entry's comment, or None."""
    if entry.comment is None:
        return None
    m = _SCOPE_RE.search(entry.comment)
    return m.group(1).lower() if m else None


@dataclass
class ScopeResult:
    scope: str
    matched: List[EnvEntry] = field(default_factory=list)
    universal: List[EnvEntry] = field(default_factory=list)
    excluded: List[EnvEntry] = field(default_factory=list)

    @property
    def entries(self) -> List[EnvEntry]:
        """All entries visible in this scope (universal + matched)."""
        return self.universal + self.matched

    def matched_count(self) -> int:
        return len(self.matched)

    def excluded_count(self) -> int:
        return len(self.excluded)

    def summary(self) -> str:
        return (
            f"Scope '{self.scope}': {len(self.entries)} entries visible "
            f"({len(self.matched)} scoped, {len(self.universal)} universal), "
            f"{len(self.excluded)} excluded."
        )

    def as_envfile(self) -> EnvFile:
        return EnvFile(entries=self.entries)


def scope_file(env_file: EnvFile, scope: str) -> ScopeResult:
    """Filter *env_file* to entries visible within *scope*."""
    scope = scope.lower()
    result = ScopeResult(scope=scope)
    for entry in env_file.entries:
        entry_scope = _entry_scope(entry)
        if entry_scope is None:
            result.universal.append(entry)
        elif entry_scope == scope:
            result.matched.append(entry)
        else:
            result.excluded.append(entry)
    return result


def all_scopes(env_file: EnvFile) -> List[str]:
    """Return a sorted list of all unique scope names declared in *env_file*."""
    scopes: Dict[str, None] = {}
    for entry in env_file.entries:
        s = _entry_scope(entry)
        if s is not None:
            scopes[s] = None
    return sorted(scopes.keys())
