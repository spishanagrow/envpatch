"""Split an EnvFile into multiple EnvFiles based on key prefixes or a mapping."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class SplitResult:
    """Result of splitting an EnvFile into named buckets."""
    buckets: Dict[str, EnvFile] = field(default_factory=dict)
    unmatched: EnvFile = field(default_factory=lambda: EnvFile(entries=[]))

    def bucket_names(self) -> List[str]:
        return list(self.buckets.keys())

    def total_matched(self) -> int:
        return sum(len(f.entries) for f in self.buckets.values())

    def total_unmatched(self) -> int:
        return len(self.unmatched.entries)

    def summary(self) -> str:
        parts = [f"{name}: {len(f.entries)} key(s)" for name, f in self.buckets.items()]
        if self.unmatched.entries:
            parts.append(f"unmatched: {len(self.unmatched.entries)} key(s)")
        return ", ".join(parts) if parts else "no entries"


def _make_bucket() -> EnvFile:
    return EnvFile(entries=[])


def split_by_prefix(
    env_file: EnvFile,
    prefixes: List[str],
    strip_prefix: bool = False,
) -> SplitResult:
    """Split entries into buckets by key prefix (longest match wins)."""
    result = SplitResult()
    sorted_prefixes = sorted(prefixes, key=len, reverse=True)

    for entry in env_file.entries:
        if entry.key is None:
            continue
        matched = False
        for prefix in sorted_prefixes:
            if entry.key.startswith(prefix):
                bucket_name = prefix.rstrip("_")
                if bucket_name not in result.buckets:
                    result.buckets[bucket_name] = _make_bucket()
                if strip_prefix:
                    new_entry = EnvEntry(
                        key=entry.key[len(prefix):],
                        value=entry.value,
                        comment=entry.comment,
                        line_number=entry.line_number,
                        raw=entry.raw,
                    )
                    result.buckets[bucket_name].entries.append(new_entry)
                else:
                    result.buckets[bucket_name].entries.append(entry)
                matched = True
                break
        if not matched:
            result.unmatched.entries.append(entry)

    return result


def split_by_map(
    env_file: EnvFile,
    key_map: Dict[str, str],
) -> SplitResult:
    """Split entries into named buckets according to an explicit key->bucket mapping."""
    result = SplitResult()

    for entry in env_file.entries:
        if entry.key is None:
            continue
        bucket_name: Optional[str] = key_map.get(entry.key)
        if bucket_name is not None:
            if bucket_name not in result.buckets:
                result.buckets[bucket_name] = _make_bucket()
            result.buckets[bucket_name].entries.append(entry)
        else:
            result.unmatched.entries.append(entry)

    return result
