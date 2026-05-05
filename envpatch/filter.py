"""Filter entries from an EnvFile by key pattern, tag, group, or secret status."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from envpatch.parser import EnvEntry, EnvFile
from envpatch.differ import is_secret


@dataclass
class FilterResult:
    matched: List[EnvEntry] = field(default_factory=list)
    excluded: List[EnvEntry] = field(default_factory=list)

    @property
    def matched_count(self) -> int:
        return len(self.matched)

    @property
    def excluded_count(self) -> int:
        return len(self.excluded)

    def summary(self) -> str:
        return (
            f"{self.matched_count} matched, {self.excluded_count} excluded"
        )

    def as_envfile(self) -> EnvFile:
        return EnvFile(entries=list(self.matched))


def filter_by_pattern(env: EnvFile, pattern: str) -> FilterResult:
    """Keep only entries whose key matches the given regex pattern."""
    rx = re.compile(pattern)
    matched = [e for e in env.entries if rx.search(e.key)]
    excluded = [e for e in env.entries if not rx.search(e.key)]
    return FilterResult(matched=matched, excluded=excluded)


def filter_by_prefix(env: EnvFile, prefix: str) -> FilterResult:
    """Keep only entries whose key starts with *prefix* (case-sensitive)."""
    matched = [e for e in env.entries if e.key.startswith(prefix)]
    excluded = [e for e in env.entries if not e.key.startswith(prefix)]
    return FilterResult(matched=matched, excluded=excluded)


def filter_secrets(env: EnvFile, *, keep_secrets: bool = True) -> FilterResult:
    """Keep secrets (or non-secrets) depending on *keep_secrets*."""
    matched = [e for e in env.entries if is_secret(e.key) == keep_secrets]
    excluded = [e for e in env.entries if is_secret(e.key) != keep_secrets]
    return FilterResult(matched=matched, excluded=excluded)


def filter_by_keys(env: EnvFile, keys: List[str]) -> FilterResult:
    """Keep only entries whose key is in the explicit *keys* list."""
    key_set = set(keys)
    matched = [e for e in env.entries if e.key in key_set]
    excluded = [e for e in env.entries if e.key not in key_set]
    return FilterResult(matched=matched, excluded=excluded)
