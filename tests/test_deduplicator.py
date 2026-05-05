"""Tests for envpatch.deduplicator."""

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.deduplicator import (
    deduplicate,
    duplicate_keys,
    has_duplicates,
    as_envfile,
    summary,
)


def _entry(key: str, value: str, line_number: int = 1, raw: str = "") -> EnvEntry:
    raw = raw or f"{key}={value}"
    return EnvEntry(key=key, value=value, line_number=line_number, raw=raw)


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries), raw="")


def test_no_duplicates_returns_empty_dict():
    f = _make_file(_entry("A", "1", 1), _entry("B", "2", 2))
    assert duplicate_keys(f) == {}


def test_duplicate_keys_detects_repeated_key():
    f = _make_file(
        _entry("A", "1", 1),
        _entry("B", "2", 2),
        _entry("A", "3", 3),
    )
    dupes = duplicate_keys(f)
    assert "A" in dupes
    assert dupes["A"] == [1, 3]


def test_has_duplicates_true():
    f = _make_file(_entry("X", "a", 1), _entry("X", "b", 2))
    assert has_duplicates(f) is True


def test_has_duplicates_false():
    f = _make_file(_entry("X", "a", 1), _entry("Y", "b", 2))
    assert has_duplicates(f) is False


def test_deduplicate_keep_last_default():
    f = _make_file(
        _entry("A", "first", 1, "A=first"),
        _entry("A", "last", 2, "A=last"),
    )
    result = deduplicate(f)
    assert len(result.entries) == 1
    assert result.entries[0].value == "last"


def test_deduplicate_keep_first():
    f = _make_file(
        _entry("A", "first", 1, "A=first"),
        _entry("A", "last", 2, "A=last"),
    )
    result = deduplicate(f, keep="first")
    assert len(result.entries) == 1
    assert result.entries[0].value == "first"


def test_deduplicate_preserves_non_key_entries():
    comment = EnvEntry(key=None, value=None, line_number=1, raw="# comment")
    f = _make_file(
        comment,
        _entry("A", "1", 2, "A=1"),
        _entry("A", "2", 3, "A=2"),
    )
    result = deduplicate(f)
    keys_and_raws = [(e.key, e.raw) for e in result.entries]
    assert (None, "# comment") in keys_and_raws


def test_deduplicate_unique_keys_unchanged():
    entries = [
        _entry("A", "1", 1, "A=1"),
        _entry("B", "2", 2, "B=2"),
        _entry("C", "3", 3, "C=3"),
    ]
    f = _make_file(*entries)
    result = deduplicate(f)
    assert len(result.entries) == 3


def test_deduplicate_invalid_keep_raises():
    f = _make_file(_entry("A", "1", 1))
    with pytest.raises(ValueError):
        deduplicate(f, keep="middle")


def test_as_envfile_renders_lines():
    f = _make_file(
        _entry("A", "1", 1, "A=1"),
        _entry("A", "2", 2, "A=2"),
    )
    result = deduplicate(f, keep="last")
    output = as_envfile(result)
    assert "A=2" in output
    assert output.count("A=") == 1


def test_summary_no_duplicates():
    f = _make_file(_entry("A", "1", 1))
    result = deduplicate(f)
    assert "No duplicate" in summary(result)


def test_summary_with_duplicates():
    f = _make_file(
        _entry("SECRET", "a", 1, "SECRET=a"),
        _entry("SECRET", "b", 2, "SECRET=b"),
    )
    result = deduplicate(f)
    msg = summary(result)
    assert "SECRET" in msg
    assert "1" in msg  # 1 duplicate removed
