"""annotator.py — attach inline comments/annotations to .env entries."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class AnnotateResult:
    entries: List[EnvEntry] = field(default_factory=list)
    annotated: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def annotated_count(self) -> int:
        return len(self.annotated)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped)

    def as_envfile(self) -> EnvFile:
        return EnvFile(entries=self.entries)

    def summary(self) -> str:
        return (
            f"Annotated {self.annotated_count} key(s), "
            f"skipped {self.skipped_count} key(s)."
        )


def _apply_annotation(entry: EnvEntry, note: str) -> EnvEntry:
    """Return a copy of *entry* with *note* appended as an inline comment."""
    existing = entry.comment or ""
    # Strip any leading '#' and whitespace from the existing inline comment
    existing_text = existing.lstrip("# ").rstrip()
    if existing_text:
        new_comment = f"# {existing_text} | {note}"
    else:
        new_comment = f"# {note}"
    return EnvEntry(
        key=entry.key,
        value=entry.value,
        comment=new_comment,
        line_number=entry.line_number,
        raw=entry.raw,
    )


def annotate_file(
    env_file: EnvFile,
    annotations: Dict[str, str],
    *,
    overwrite: bool = False,
) -> AnnotateResult:
    """Attach annotations to matching keys in *env_file*.

    Parameters
    ----------
    env_file:    Source EnvFile whose entries will be annotated.
    annotations: Mapping of key -> annotation text to apply.
    overwrite:   When True, replace any existing inline comment entirely.
                 When False (default), append to the existing comment.
    """
    result = AnnotateResult()

    for entry in env_file.entries:
        if not hasattr(entry, "key") or entry.key is None:
            # Preserve comment-only / blank lines unchanged
            result.entries.append(entry)
            continue

        if entry.key in annotations:
            note = annotations[entry.key]
            if overwrite:
                annotated = EnvEntry(
                    key=entry.key,
                    value=entry.value,
                    comment=f"# {note}",
                    line_number=entry.line_number,
                    raw=entry.raw,
                )
            else:
                annotated = _apply_annotation(entry, note)
            result.entries.append(annotated)
            result.annotated.append(entry.key)
        else:
            result.entries.append(entry)
            result.skipped.append(entry.key)

    return result
