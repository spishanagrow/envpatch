"""Tests for envpatch.patcher — apply_patch."""

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.differ import DiffEntry, ChangeType
from envpatch.patcher import apply_patch, PatchResult


def _entry(key: str, value: str) -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=None, line_number=1)


def _make_file(*pairs) -> EnvFile:
    entries = [_entry(k, v) for k, v in pairs]
    return EnvFile(entries=entries, raw="")


def _diff(change_type: ChangeType, key: str, old=None, new=None) -> DiffEntry:
    return DiffEntry(change_type=change_type, key=key, old_value=old, new_value=new)


# ---------------------------------------------------------------------------
# apply ADDED
# ---------------------------------------------------------------------------

def test_apply_patch_adds_new_key():
    base = _make_file(("A", "1"))
    patch = [_diff(ChangeType.ADDED, "B", new="2")]
    result = apply_patch(base, patch)
    keys = [e.key for e in result.file.entries]
    assert "B" in keys
    assert result.applied_count == 1


def test_apply_patch_added_key_overwrites_if_exists():
    base = _make_file(("A", "old"))
    patch = [_diff(ChangeType.ADDED, "A", new="new")]
    result = apply_patch(base, patch)
    assert result.file.entries[0].value == "new"
    assert result.applied_count == 1


# ---------------------------------------------------------------------------
# apply MODIFIED
# ---------------------------------------------------------------------------

def test_apply_patch_modifies_existing_key():
    base = _make_file(("DB_HOST", "localhost"), ("PORT", "5432"))
    patch = [_diff(ChangeType.MODIFIED, "DB_HOST", old="localhost", new="prod.db")]
    result = apply_patch(base, patch)
    values = {e.key: e.value for e in result.file.entries}
    assert values["DB_HOST"] == "prod.db"
    assert result.applied_count == 1


def test_apply_patch_modified_missing_key_skipped_by_default():
    base = _make_file(("A", "1"))
    patch = [_diff(ChangeType.MODIFIED, "MISSING", old="x", new="y")]
    result = apply_patch(base, patch)
    assert result.skipped_count == 1
    assert result.applied_count == 0


def test_apply_patch_modified_missing_key_raises_when_not_skip():
    base = _make_file(("A", "1"))
    patch = [_diff(ChangeType.MODIFIED, "MISSING", old="x", new="y")]
    with pytest.raises(KeyError, match="MISSING"):
        apply_patch(base, patch, skip_missing=False)


# ---------------------------------------------------------------------------
# apply REMOVED
# ---------------------------------------------------------------------------

def test_apply_patch_removes_key():
    base = _make_file(("A", "1"), ("B", "2"))
    patch = [_diff(ChangeType.REMOVED, "A")]
    result = apply_patch(base, patch)
    keys = [e.key for e in result.file.entries]
    assert "A" not in keys
    assert "B" in keys
    assert result.applied_count == 1


def test_apply_patch_removed_missing_key_skipped_by_default():
    base = _make_file(("A", "1"))
    patch = [_diff(ChangeType.REMOVED, "GHOST")]
    result = apply_patch(base, patch)
    assert result.skipped_count == 1


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------

def test_summary_no_changes():
    base = _make_file(("A", "1"))
    result = apply_patch(base, [])
    assert result.summary() == "No changes applied"


def test_summary_with_applied_and_skipped():
    base = _make_file(("A", "1"))
    patch = [
        _diff(ChangeType.ADDED, "B", new="2"),
        _diff(ChangeType.MODIFIED, "MISSING", old="x", new="y"),
    ]
    result = apply_patch(base, patch)
    s = result.summary()
    assert "applied" in s
    assert "skipped" in s
