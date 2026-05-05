"""Tests for envpatch.flattener."""

from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.flattener import flatten_file, expand_dict, FlattenResult


def _entry(key: str, value: str, line: int = 1) -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=None, line=line)


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries), raw="")


# ---------------------------------------------------------------------------
# flatten_file
# ---------------------------------------------------------------------------

def test_flatten_simple_keys_are_top_level():
    f = _make_file(_entry("HOST", "localhost"), _entry("PORT", "5432"))
    result = flatten_file(f)
    assert result.nested == {"HOST": "localhost", "PORT": "5432"}


def test_flatten_splits_on_double_underscore():
    f = _make_file(_entry("DB__HOST", "localhost"), _entry("DB__PORT", "5432"))
    result = flatten_file(f)
    assert result.nested == {"DB": {"HOST": "localhost", "PORT": "5432"}}


def test_flatten_three_level_key():
    f = _make_file(_entry("APP__DB__HOST", "db.local"))
    result = flatten_file(f)
    assert result.nested["APP"]["DB"]["HOST"] == "db.local"


def test_flatten_custom_separator():
    f = _make_file(_entry("APP.HOST", "web"), _entry("APP.PORT", "80"))
    result = flatten_file(f, separator=".")
    assert result.nested == {"APP": {"HOST": "web", "PORT": "80"}}


def test_flatten_preserves_entries_list():
    entries = [_entry("DB__HOST", "localhost"), _entry("APP_KEY", "secret")]
    f = _make_file(*entries)
    result = flatten_file(f)
    assert len(result.entries) == 2
    assert result.keys() == ["DB__HOST", "APP_KEY"]


def test_flatten_result_is_flatten_result_instance():
    f = _make_file(_entry("KEY", "val"))
    result = flatten_file(f)
    assert isinstance(result, FlattenResult)


def test_flatten_summary_contains_group_count():
    f = _make_file(_entry("DB__HOST", "h"), _entry("DB__PORT", "5432"), _entry("APP_KEY", "k"))
    result = flatten_file(f)
    summary = result.summary()
    assert "2" in summary  # two top-level groups: DB, APP_KEY


def test_flatten_empty_file_returns_empty_nested():
    f = _make_file()
    result = flatten_file(f)
    assert result.nested == {}
    assert result.entries == []


# ---------------------------------------------------------------------------
# expand_dict
# ---------------------------------------------------------------------------

def test_expand_flat_dict_returns_entries():
    data = {"HOST": "localhost", "PORT": "5432"}
    entries = expand_dict(data)
    keys = {e.key for e in entries}
    assert keys == {"HOST", "PORT"}


def test_expand_nested_dict_produces_flat_keys():
    data = {"DB": {"HOST": "localhost", "PORT": "5432"}}
    entries = expand_dict(data)
    keys = {e.key for e in entries}
    assert "DB__HOST" in keys
    assert "DB__PORT" in keys


def test_expand_uses_custom_separator():
    data = {"APP": {"KEY": "secret"}}
    entries = expand_dict(data, separator=".")
    assert entries[0].key == "APP.KEY"


def test_expand_roundtrip():
    original_entries = [
        _entry("DB__HOST", "localhost"),
        _entry("DB__PORT", "5432"),
        _entry("APP_KEY", "abc"),
    ]
    f = _make_file(*original_entries)
    result = flatten_file(f)
    expanded = expand_dict(result.nested)
    keys = {e.key for e in expanded}
    assert {"DB__HOST", "DB__PORT", "APP_KEY"} == keys
