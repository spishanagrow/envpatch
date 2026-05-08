"""Tests for envpatch.annotator."""
import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.annotator import annotate_file, AnnotateResult


def _entry(
    key: str,
    value: str = "val",
    comment: Optional[str] = None,
    line_number: int = 1,
) -> EnvEntry:
    from typing import Optional
    return EnvEntry(key=key, value=value, comment=comment, line_number=line_number, raw=f"{key}={value}")


from typing import Optional


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# annotated_count / skipped_count
# ---------------------------------------------------------------------------

def test_annotated_count_reflects_matched_keys():
    f = _make_file(_entry("DB_HOST"), _entry("APP_PORT"))
    result = annotate_file(f, {"DB_HOST": "primary database host"})
    assert result.annotated_count == 1


def test_skipped_count_reflects_unmatched_keys():
    f = _make_file(_entry("DB_HOST"), _entry("APP_PORT"))
    result = annotate_file(f, {"DB_HOST": "note"})
    assert result.skipped_count == 1


# ---------------------------------------------------------------------------
# comment content
# ---------------------------------------------------------------------------

def test_annotation_appended_as_inline_comment():
    f = _make_file(_entry("DB_HOST"))
    result = annotate_file(f, {"DB_HOST": "primary host"})
    annotated_entry = result.entries[0]
    assert "primary host" in (annotated_entry.comment or "")


def test_annotation_prefixed_with_hash():
    f = _make_file(_entry("DB_HOST"))
    result = annotate_file(f, {"DB_HOST": "note"})
    assert (result.entries[0].comment or "").startswith("#")


def test_existing_comment_preserved_when_not_overwriting():
    entry = _entry("DB_HOST", comment="# existing")
    f = _make_file(entry)
    result = annotate_file(f, {"DB_HOST": "new note"})
    comment = result.entries[0].comment or ""
    assert "existing" in comment
    assert "new note" in comment


def test_overwrite_replaces_existing_comment():
    entry = _entry("DB_HOST", comment="# old note")
    f = _make_file(entry)
    result = annotate_file(f, {"DB_HOST": "fresh note"}, overwrite=True)
    comment = result.entries[0].comment or ""
    assert "old note" not in comment
    assert "fresh note" in comment


# ---------------------------------------------------------------------------
# unannotated entries unchanged
# ---------------------------------------------------------------------------

def test_unannotated_entry_value_unchanged():
    f = _make_file(_entry("APP_PORT", value="8080"))
    result = annotate_file(f, {})
    assert result.entries[0].value == "8080"


def test_unannotated_entry_key_unchanged():
    f = _make_file(_entry("APP_PORT"))
    result = annotate_file(f, {})
    assert result.entries[0].key == "APP_PORT"


# ---------------------------------------------------------------------------
# as_envfile / summary
# ---------------------------------------------------------------------------

def test_as_envfile_returns_envfile_instance():
    f = _make_file(_entry("DB_HOST"))
    result = annotate_file(f, {"DB_HOST": "note"})
    assert isinstance(result.as_envfile(), EnvFile)


def test_summary_contains_counts():
    f = _make_file(_entry("DB_HOST"), _entry("APP_PORT"))
    result = annotate_file(f, {"DB_HOST": "note"})
    s = result.summary()
    assert "1" in s  # annotated
    assert "1" in s  # skipped (both appear)
