"""Tests for envpatch.renamer."""

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.renamer import rename_keys, summary


def _entry(key: str, value: str, line: int = 1) -> EnvEntry:
    return EnvEntry(
        key=key,
        value=value,
        raw_line=f"{key}={value}",
        line_number=line,
        comment=None,
        is_quoted=False,
    )


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(path=".env", entries=list(entries))


def test_rename_single_key():
    f = _make_file(_entry("OLD_KEY", "value"))
    result = rename_keys(f, {"OLD_KEY": "NEW_KEY"})
    keys = [e.key for e in result.entries]
    assert "NEW_KEY" in keys
    assert "OLD_KEY" not in keys
    assert result.renamed == {"OLD_KEY": "NEW_KEY"}


def test_rename_preserves_value():
    f = _make_file(_entry("DB_HOST", "localhost"))
    result = rename_keys(f, {"DB_HOST": "DATABASE_HOST"})
    entry = result.entries[0]
    assert entry.value == "localhost"


def test_rename_preserves_order():
    f = _make_file(
        _entry("A", "1", 1),
        _entry("B", "2", 2),
        _entry("C", "3", 3),
    )
    result = rename_keys(f, {"B": "BETA"})
    assert [e.key for e in result.entries] == ["A", "BETA", "C"]


def test_rename_skips_missing_key():
    f = _make_file(_entry("PRESENT", "yes"))
    result = rename_keys(f, {"MISSING": "RENAMED"})
    assert "MISSING" in result.skipped
    assert result.skipped["MISSING"] == "key not found"


def test_rename_skips_when_target_exists():
    f = _make_file(_entry("OLD", "1"), _entry("NEW", "2"))
    result = rename_keys(f, {"OLD": "NEW"})
    assert "OLD" in result.skipped
    assert "already exists" in result.skipped["OLD"]
    # Both original keys must still be present
    keys = [e.key for e in result.entries]
    assert "OLD" in keys
    assert "NEW" in keys


def test_rename_multiple_keys():
    f = _make_file(_entry("A", "1"), _entry("B", "2"), _entry("C", "3"))
    result = rename_keys(f, {"A": "ALPHA", "C": "GAMMA"})
    keys = [e.key for e in result.entries]
    assert keys == ["ALPHA", "B", "GAMMA"]
    assert len(result.renamed) == 2


def test_as_envfile_returns_envfile():
    f = _make_file(_entry("X", "42"))
    result = rename_keys(f, {"X": "Y"})
    env = result.as_envfile(f)
    assert env.path == ".env"
    assert env.entries[0].key == "Y"


def test_summary_shows_renamed_and_skipped():
    f = _make_file(_entry("OLD", "v"))
    result = rename_keys(f, {"OLD": "NEW", "GHOST": "X"})
    s = summary(result)
    assert "OLD -> NEW" in s
    assert "GHOST" in s


def test_summary_empty_when_no_renames():
    f = _make_file(_entry("KEY", "val"))
    result = rename_keys(f, {})
    assert summary(result) == "No renames applied."
