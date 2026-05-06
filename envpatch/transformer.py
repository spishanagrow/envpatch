"""Transform .env values using built-in or custom functions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from envpatch.parser import EnvEntry, EnvFile


TransformFn = Callable[[str], str]

_BUILTINS: Dict[str, TransformFn] = {
    "upper": str.upper,
    "lower": str.lower,
    "strip": str.strip,
    "trim": str.strip,
}


@dataclass
class TransformResult:
    entries: List[EnvEntry]
    transformed_keys: List[str] = field(default_factory=list)
    skipped_keys: List[str] = field(default_factory=list)

    def as_envfile(self) -> EnvFile:
        return EnvFile(entries=self.entries)

    def transformed_count(self) -> int:
        return len(self.transformed_keys)

    def skipped_count(self) -> int:
        return len(self.skipped_keys)

    def summary(self) -> str:
        return (
            f"Transformed {self.transformed_count()} key(s), "
            f"skipped {self.skipped_count()} key(s)."
        )


def _resolve_fn(transform: str | TransformFn) -> Optional[TransformFn]:
    if callable(transform):
        return transform
    return _BUILTINS.get(str(transform))


def transform_file(
    env_file: EnvFile,
    transform: str | TransformFn,
    keys: Optional[List[str]] = None,
    secrets_only: bool = False,
) -> TransformResult:
    """Apply *transform* to values in *env_file*.

    Args:
        env_file: Parsed .env file.
        transform: Named built-in (``'upper'``, ``'lower'``, ``'strip'``)
            or any callable ``str -> str``.
        keys: Restrict transformation to these key names.  ``None`` means all.
        secrets_only: When ``True`` only transform keys flagged as secrets.
    """
    from envpatch.differ import is_secret  # local import avoids circular

    fn = _resolve_fn(transform)
    if fn is None:
        raise ValueError(f"Unknown transform {transform!r}. "
                         f"Built-ins: {list(_BUILTINS)}")

    transformed: List[str] = []
    skipped: List[str] = []
    new_entries: List[EnvEntry] = []

    for entry in env_file.entries:
        if entry.key is None:
            new_entries.append(entry)
            continue

        want_key = keys is None or entry.key in keys
        want_secret = (not secrets_only) or is_secret(entry.key)

        if want_key and want_secret:
            new_val = fn(entry.value or "")
            new_entries.append(
                EnvEntry(
                    key=entry.key,
                    value=new_val,
                    comment=entry.comment,
                    line_number=entry.line_number,
                    raw=entry.raw,
                )
            )
            transformed.append(entry.key)
        else:
            new_entries.append(entry)
            skipped.append(entry.key)

    return TransformResult(
        entries=new_entries,
        transformed_keys=transformed,
        skipped_keys=skipped,
    )
