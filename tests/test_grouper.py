"""Tests for envpatch.grouper."""
import pytest
from envpatch.parser import EnvEntry, EnvFile
from envpatch.grouper import GroupResult, group_by_prefix, group_by_map


def _entry(key: str, value: str = "val") -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", line_number=1)


def _make_file(*keys: str) -> EnvFile:
    entries = [_entry(k) for k in keys]
    return EnvFile(entries=entries, raw="")


# --- group_by_prefix ---

def test_prefix_groups_db_keys():
    f = _make_file("DB_HOST", "DB_PORT", "APP_NAME")
    result = group_by_prefix(f)
    assert "DB" in result.groups
    assert len(result.entries_for("DB")) == 2


def test_prefix_groups_app_keys():
    f = _make_file("APP_NAME", "APP_ENV", "SECRET_KEY")
    result = group_by_prefix(f)
    assert "APP" in result.groups
    assert len(result.entries_for("APP")) == 2


def test_prefix_ungrouped_when_no_separator():
    f = _make_file("HOST", "PORT")
    result = group_by_prefix(f)
    assert len(result.ungrouped) == 2
    assert result.groups == {}


def test_prefix_min_group_size_demotes_small_groups():
    f = _make_file("DB_HOST", "APP_NAME", "APP_ENV")
    result = group_by_prefix(f, min_group_size=2)
    assert "DB" not in result.groups
    assert "APP" in result.groups
    # DB_HOST should be ungrouped
    ungrouped_keys = [e.key for e in result.ungrouped]
    assert "DB_HOST" in ungrouped_keys


def test_group_names_are_sorted():
    f = _make_file("Z_ONE", "A_TWO", "M_THREE")
    result = group_by_prefix(f)
    assert result.group_names() == ["A", "M", "Z"]


def test_total_grouped_count():
    f = _make_file("DB_HOST", "DB_PORT", "APP_NAME")
    result = group_by_prefix(f)
    assert result.total_grouped() == 3


# --- group_by_map ---

def test_map_assigns_keys_to_groups():
    f = _make_file("DB_HOST", "SECRET_KEY", "APP_NAME")
    result = group_by_map(f, {"database": ["DB_HOST"], "app": ["APP_NAME"]})
    assert "database" in result.groups
    assert "app" in result.groups
    assert len(result.ungrouped) == 1
    assert result.ungrouped[0].key == "SECRET_KEY"


def test_map_unknown_keys_go_ungrouped():
    f = _make_file("UNKNOWN")
    result = group_by_map(f, {"g": ["OTHER"]})
    assert result.ungrouped[0].key == "UNKNOWN"


def test_map_empty_map_all_ungrouped():
    f = _make_file("A", "B")
    result = group_by_map(f, {})
    assert len(result.ungrouped) == 2
    assert result.groups == {}


# --- GroupResult helpers ---

def test_summary_string():
    f = _make_file("DB_HOST", "DB_PORT")
    result = group_by_prefix(f)
    s = result.summary()
    assert "DB" in s
    assert "ungrouped" in s
