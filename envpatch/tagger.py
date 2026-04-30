"""Tag .env entries with arbitrary labels for grouping and filtering."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from envpatch.parser import EnvEntry, EnvFile

TAG_PREFIX = "# @tags:"


@dataclass
class TagResult:
    entries: List[EnvEntry]
    tag_map: Dict[str, Set[str]]  # key -> set of tags

    def tags_for(self, key: str) -> Set[str]:
        return self.tag_map.get(key, set())

    def keys_with_tag(self, tag: str) -> List[str]:
        return [k for k, tags in self.tag_map.items() if tag in tags]

    def all_tags(self) -> Set[str]:
        result: Set[str] = set()
        for tags in self.tag_map.values():
            result |= tags
        return result

    def summary(self) -> str:
        total = sum(len(t) for t in self.tag_map.values())
        return f"{len(self.tag_map)} tagged keys, {total} total tag(s), {len(self.all_tags())} unique tag(s)"


def _parse_tags_from_comment(comment: Optional[str]) -> Set[str]:
    """Extract tags from an inline or preceding comment like '# @tags: foo, bar'."""
    if not comment:
        return set()
    lower = comment.strip()
    if not lower.startswith("@tags:"):
        return set()
    raw = lower[len("@tags:"):].strip()
    return {t.strip() for t in raw.split(",") if t.strip()}


def tag_file(env_file: EnvFile, tag_map: Dict[str, Set[str]]) -> TagResult:
    """Apply an explicit tag_map to entries, merging with any embedded tag comments."""
    result_map: Dict[str, Set[str]] = {}
    for entry in env_file.entries:
        existing = _parse_tags_from_comment(entry.comment)
        extra = tag_map.get(entry.key, set())
        merged = existing | extra
        if merged:
            result_map[entry.key] = merged
    return TagResult(entries=env_file.entries, tag_map=result_map)


def filter_by_tag(result: TagResult, tag: str) -> List[EnvEntry]:
    """Return only entries that carry the given tag."""
    tagged_keys = result.keys_with_tag(tag)
    return [e for e in result.entries if e.key in tagged_keys]
