"""Tests for envpatch.pinner."""

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.pinner import PinResult, is_pinned, pin_keys


def _entry(key: str, value: str = "val", comment: str = "") -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=comment, line_number=1)


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# is_pinned
# ---------------------------------------------------------------------------

def test_is_pinned_returns_false_for_plain_entry():
    assert is_pinned(_entry("API_KEY")) is False


def test_is_pinned_returns_true_after_marking():
    entry = _entry("API_KEY", comment="# pinned")
    assert is_pinned(entry) is True


def test_is_pinned_detects_marker_within_longer_comment():
    entry = _entry("DB_PASS", comment="do not change # pinned here")
    assert is_pinned(entry) is True


# ---------------------------------------------------------------------------
# pin_keys
# ---------------------------------------------------------------------------

def test_pin_keys_marks_existing_key():
    f = _make_file(_entry("SECRET", "abc"))
    result = pin_keys(f, ["SECRET"])
    assert "SECRET" in result.pinned
    assert result.skipped == []


def test_pin_keys_entry_is_marked_in_result_file():
    f = _make_file(_entry("TOKEN", "xyz"))
    result = pin_keys(f, ["TOKEN"])
    token_entry = next(e for e in result.file.entries if e.key == "TOKEN")
    assert is_pinned(token_entry)


def test_pin_keys_unknown_key_goes_to_skipped():
    f = _make_file(_entry("KNOWN", "1"))
    result = pin_keys(f, ["UNKNOWN"])
    assert "UNKNOWN" in result.skipped
    assert result.pinned == []


def test_pin_keys_preserves_existing_comment():
    f = _make_file(_entry("DB_URL", "postgres://", comment="# keep"))
    result = pin_keys(f, ["DB_URL"])
    db_entry = next(e for e in result.file.entries if e.key == "DB_URL")
    assert "# keep" in db_entry.comment
    assert "# pinned" in db_entry.comment


def test_pin_keys_does_not_duplicate_marker_on_already_pinned():
    f = _make_file(_entry("X", "1", comment="# pinned"))
    result = pin_keys(f, ["X"])
    assert result.file.entries[0].comment.count("# pinned") == 1


def test_pin_keys_summary_string():
    f = _make_file(_entry("A"), _entry("B"))
    result = pin_keys(f, ["A", "MISSING"])
    summary = result.summary()
    assert "1" in summary
    assert "Pinned" in summary


def test_pin_keys_counts():
    f = _make_file(_entry("A"), _entry("B"))
    result = pin_keys(f, ["A", "B", "C"])
    assert result.pinned_count() == 2
    assert result.skipped_count() == 1
