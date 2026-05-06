"""Tests for envpatch.transformer."""

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.transformer import TransformResult, transform_file


def _entry(key: str, value: str, comment: str = "") -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=comment, line_number=1, raw="")


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# Basic transforms
# ---------------------------------------------------------------------------

def test_upper_transforms_value():
    f = _make_file(_entry("GREETING", "hello"))
    result = transform_file(f, "upper")
    vals = {e.key: e.value for e in result.entries if e.key}
    assert vals["GREETING"] == "HELLO"


def test_lower_transforms_value():
    f = _make_file(_entry("MODE", "PRODUCTION"))
    result = transform_file(f, "lower")
    vals = {e.key: e.value for e in result.entries if e.key}
    assert vals["MODE"] == "production"


def test_strip_removes_whitespace():
    f = _make_file(_entry("HOST", "  localhost  "))
    result = transform_file(f, "strip")
    vals = {e.key: e.value for e in result.entries if e.key}
    assert vals["HOST"] == "localhost"


def test_custom_callable_applied():
    f = _make_file(_entry("TAG", "v1.2.3"))
    result = transform_file(f, lambda v: v.replace(".", "_"))
    vals = {e.key: e.value for e in result.entries if e.key}
    assert vals["TAG"] == "v1_2_3"


# ---------------------------------------------------------------------------
# Key filtering
# ---------------------------------------------------------------------------

def test_keys_filter_limits_transformation():
    f = _make_file(_entry("A", "hello"), _entry("B", "world"))
    result = transform_file(f, "upper", keys=["A"])
    vals = {e.key: e.value for e in result.entries if e.key}
    assert vals["A"] == "HELLO"
    assert vals["B"] == "world"  # untouched


def test_skipped_keys_recorded():
    f = _make_file(_entry("A", "x"), _entry("B", "y"))
    result = transform_file(f, "upper", keys=["A"])
    assert "B" in result.skipped_keys


# ---------------------------------------------------------------------------
# secrets_only flag
# ---------------------------------------------------------------------------

def test_secrets_only_skips_plain_keys():
    f = _make_file(_entry("APP_NAME", "myapp"), _entry("SECRET_KEY", "abc"))
    result = transform_file(f, "upper", secrets_only=True)
    vals = {e.key: e.value for e in result.entries if e.key}
    assert vals["APP_NAME"] == "myapp"  # not a secret — unchanged
    assert vals["SECRET_KEY"] == "ABC"


# ---------------------------------------------------------------------------
# Result helpers
# ---------------------------------------------------------------------------

def test_transformed_count():
    f = _make_file(_entry("A", "x"), _entry("B", "y"))
    result = transform_file(f, "upper")
    assert result.transformed_count() == 2


def test_summary_string():
    f = _make_file(_entry("A", "x"))
    result = transform_file(f, "upper")
    assert "Transformed" in result.summary()


def test_as_envfile_returns_envfile():
    from envpatch.parser import EnvFile
    f = _make_file(_entry("A", "x"))
    result = transform_file(f, "upper")
    assert isinstance(result.as_envfile(), EnvFile)


def test_unknown_transform_raises():
    f = _make_file(_entry("A", "x"))
    with pytest.raises(ValueError, match="Unknown transform"):
        transform_file(f, "rot13")


def test_comment_entries_passed_through():
    comment_entry = EnvEntry(key=None, value=None, comment="# section", line_number=1, raw="# section")
    f = EnvFile(entries=[comment_entry, _entry("A", "hello")])
    result = transform_file(f, "upper")
    assert result.entries[0].key is None  # comment preserved
