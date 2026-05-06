"""Tests for envpatch.normalizer."""

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.normalizer import normalize_file, NormalizeResult


def _entry(key, value="value", line_number=1, comment=None):
    raw = f"{key}={value}"
    return EnvEntry(key=key, value=value, comment=comment, line_number=line_number, raw=raw)


def _make_file(*entries):
    return EnvFile(entries=list(entries))


def test_normalize_uppercases_keys():
    f = _make_file(_entry("db_host", "localhost"))
    result = normalize_file(f, uppercase_keys=True, strip_values=False)
    assert result.entries[0].key == "DB_HOST"


def test_normalize_records_uppercased_key():
    f = _make_file(_entry("db_host", "localhost"))
    result = normalize_file(f)
    assert "DB_HOST" in result.normalized_keys


def test_normalize_strips_value_whitespace():
    f = _make_file(_entry("APP_NAME", "  myapp  "))
    result = normalize_file(f, uppercase_keys=False, strip_values=True)
    assert result.entries[0].value == "myapp"


def test_normalize_records_stripped_value_key():
    f = _make_file(_entry("APP_NAME", "  myapp  "))
    result = normalize_file(f)
    assert "APP_NAME" in result.normalized_values


def test_normalize_skips_already_clean_entry():
    f = _make_file(_entry("APP_NAME", "clean"))
    result = normalize_file(f)
    assert "APP_NAME" in result.skipped
    assert result.skipped_count() == 1


def test_normalize_uppercase_false_leaves_key_unchanged():
    f = _make_file(_entry("db_host", "localhost"))
    result = normalize_file(f, uppercase_keys=False, strip_values=False)
    assert result.entries[0].key == "db_host"
    assert "db_host" in result.skipped


def test_normalize_strip_false_leaves_value_unchanged():
    f = _make_file(_entry("KEY", "  spaced  "))
    result = normalize_file(f, uppercase_keys=False, strip_values=False)
    assert result.entries[0].value == "  spaced  "


def test_normalize_passes_through_comment_entries():
    comment_entry = EnvEntry(key=None, value=None, comment="# a comment", line_number=1, raw="# a comment")
    f = _make_file(comment_entry)
    result = normalize_file(f)
    assert result.entries[0].comment == "# a comment"
    assert result.entries[0].key is None


def test_normalize_summary_nothing():
    f = _make_file(_entry("KEY", "val"))
    result = normalize_file(f)
    assert result.summary() == "nothing to normalize"


def test_normalize_summary_with_changes():
    f = _make_file(_entry("lower_key", "  spaced  "))
    result = normalize_file(f)
    summary = result.summary()
    assert "uppercased" in summary
    assert "stripped" in summary


def test_as_envfile_returns_envfile():
    f = _make_file(_entry("KEY", "val"))
    result = normalize_file(f)
    ef = result.as_envfile()
    assert isinstance(ef, EnvFile)
    assert ef.entries == result.entries


def test_normalize_multiple_entries():
    f = _make_file(
        _entry("db_host", "localhost", line_number=1),
        _entry("DB_PORT", "5432", line_number=2),
        _entry("app_name", "  envpatch  ", line_number=3),
    )
    result = normalize_file(f)
    keys = [e.key for e in result.entries if e.key]
    assert "DB_HOST" in keys
    assert "DB_PORT" in keys
    assert "APP_NAME" in keys
    assert result.entries[2].value == "envpatch"
