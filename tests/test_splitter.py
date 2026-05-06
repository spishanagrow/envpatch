"""Tests for envpatch.splitter."""
import pytest
from envpatch.parser import EnvEntry, EnvFile
from envpatch.splitter import split_by_prefix, split_by_map, SplitResult


def _entry(key: str, value: str = "val") -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=None, line_number=1, raw=f"{key}={value}")


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# --- split_by_prefix ---

def test_prefix_groups_db_keys():
    f = _make_file(_entry("DB_HOST"), _entry("DB_PORT"), _entry("APP_NAME"))
    result = split_by_prefix(f, ["DB_", "APP_"])
    assert "DB" in result.bucket_names()
    assert len(result.buckets["DB"].entries) == 2


def test_prefix_groups_app_keys():
    f = _make_file(_entry("APP_NAME"), _entry("APP_ENV"), _entry("DB_HOST"))
    result = split_by_prefix(f, ["APP_", "DB_"])
    assert len(result.buckets["APP"].entries) == 2


def test_prefix_unmatched_when_no_prefix_matches():
    f = _make_file(_entry("REDIS_URL"), _entry("APP_NAME"))
    result = split_by_prefix(f, ["APP_"])
    assert result.total_unmatched() == 1
    assert result.unmatched.entries[0].key == "REDIS_URL"


def test_prefix_longest_match_wins():
    f = _make_file(_entry("APP_DB_HOST"), _entry("APP_NAME"))
    result = split_by_prefix(f, ["APP_", "APP_DB_"])
    assert "APP_DB" in result.buckets
    assert result.buckets["APP_DB"].entries[0].key == "APP_DB_HOST"


def test_strip_prefix_renames_key():
    f = _make_file(_entry("DB_HOST", "localhost"))
    result = split_by_prefix(f, ["DB_"], strip_prefix=True)
    assert result.buckets["DB"].entries[0].key == "HOST"


def test_strip_prefix_preserves_value():
    f = _make_file(_entry("DB_PORT", "5432"))
    result = split_by_prefix(f, ["DB_"], strip_prefix=True)
    assert result.buckets["DB"].entries[0].value == "5432"


def test_total_matched_count():
    f = _make_file(_entry("DB_HOST"), _entry("DB_PORT"), _entry("OTHER"))
    result = split_by_prefix(f, ["DB_"])
    assert result.total_matched() == 2


# --- split_by_map ---

def test_map_routes_keys_to_named_buckets():
    f = _make_file(_entry("SECRET_KEY"), _entry("DEBUG"), _entry("DB_HOST"))
    mapping = {"SECRET_KEY": "secrets", "DB_HOST": "database"}
    result = split_by_map(f, mapping)
    assert "secrets" in result.buckets
    assert result.buckets["secrets"].entries[0].key == "SECRET_KEY"


def test_map_unmatched_keys_go_to_unmatched():
    f = _make_file(_entry("DEBUG"), _entry("SECRET_KEY"))
    result = split_by_map(f, {"SECRET_KEY": "secrets"})
    assert result.total_unmatched() == 1
    assert result.unmatched.entries[0].key == "DEBUG"


def test_map_multiple_keys_same_bucket():
    f = _make_file(_entry("DB_HOST"), _entry("DB_PORT"), _entry("APP_NAME"))
    mapping = {"DB_HOST": "db", "DB_PORT": "db", "APP_NAME": "app"}
    result = split_by_map(f, mapping)
    assert len(result.buckets["db"].entries) == 2


# --- SplitResult helpers ---

def test_summary_non_empty():
    f = _make_file(_entry("DB_HOST"), _entry("OTHER"))
    result = split_by_prefix(f, ["DB_"])
    s = result.summary()
    assert "DB" in s
    assert "unmatched" in s


def test_summary_empty_file():
    result = split_by_prefix(EnvFile(entries=[]), ["DB_"])
    assert result.summary() == "no entries"
