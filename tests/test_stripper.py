"""Tests for envpatch.stripper."""

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.stripper import strip_keys, StripResult


def _entry(key: str, value: str = "val", line: int = 1) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", line=line)


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries), path=".env")


# ---------------------------------------------------------------------------
# strip by exact key name
# ---------------------------------------------------------------------------

def test_strip_single_key_by_name():
    f = _make_file(_entry("DB_PASS"), _entry("APP_PORT"))
    result = strip_keys(f, keys=["DB_PASS"])
    assert "DB_PASS" not in [e.key for e in result.stripped.entries]
    assert "APP_PORT" in [e.key for e in result.stripped.entries]


def test_strip_multiple_keys_by_name():
    f = _make_file(_entry("A"), _entry("B"), _entry("C"))
    result = strip_keys(f, keys=["A", "C"])
    keys = [e.key for e in result.stripped.entries]
    assert "A" not in keys
    assert "C" not in keys
    assert "B" in keys


def test_removed_keys_list_populated():
    f = _make_file(_entry("SECRET"), _entry("SAFE"))
    result = strip_keys(f, keys=["SECRET"])
    assert result.removed_keys == ["SECRET"]


def test_skipped_keys_list_populated():
    f = _make_file(_entry("SECRET"), _entry("SAFE"))
    result = strip_keys(f, keys=["SECRET"])
    assert "SAFE" in result.skipped_keys


# ---------------------------------------------------------------------------
# strip by prefix
# ---------------------------------------------------------------------------

def test_strip_by_prefix_removes_matching_keys():
    f = _make_file(_entry("DB_HOST"), _entry("DB_PASS"), _entry("APP_KEY"))
    result = strip_keys(f, prefix="DB_")
    keys = [e.key for e in result.stripped.entries]
    assert "DB_HOST" not in keys
    assert "DB_PASS" not in keys
    assert "APP_KEY" in keys


# ---------------------------------------------------------------------------
# strip by pattern
# ---------------------------------------------------------------------------

def test_strip_by_pattern_removes_matching_keys():
    f = _make_file(_entry("AWS_SECRET_KEY"), _entry("AWS_ACCESS_KEY"), _entry("PORT"))
    result = strip_keys(f, pattern=r"SECRET")
    keys = [e.key for e in result.stripped.entries]
    assert "AWS_SECRET_KEY" not in keys
    assert "AWS_ACCESS_KEY" in keys
    assert "PORT" in keys


def test_invalid_pattern_does_not_raise():
    f = _make_file(_entry("KEY"))
    # Should not raise even with a broken regex
    result = strip_keys(f, pattern="[invalid")
    assert result.removed_count() == 0


# ---------------------------------------------------------------------------
# comments and blank lines preserved
# ---------------------------------------------------------------------------

def test_comment_entries_are_preserved():
    comment = EnvEntry(key=None, value=None, raw="# section header", line=1)
    f = _make_file(comment, _entry("DB_PASS", line=2))
    result = strip_keys(f, keys=["DB_PASS"])
    raws = [e.raw for e in result.stripped.entries]
    assert "# section header" in raws


# ---------------------------------------------------------------------------
# summary / counts
# ---------------------------------------------------------------------------

def test_summary_string_reflects_counts():
    f = _make_file(_entry("A"), _entry("B"), _entry("C"))
    result = strip_keys(f, keys=["A", "B"])
    assert "2" in result.summary()
    assert result.removed_count() == 2


def test_no_matching_keys_returns_original_entries():
    f = _make_file(_entry("X"), _entry("Y"))
    result = strip_keys(f, keys=["Z"])
    assert result.removed_count() == 0
    assert len(result.stripped.entries) == 2
