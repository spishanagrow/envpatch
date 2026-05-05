"""Tests for envpatch.filter."""

import pytest
from envpatch.parser import EnvEntry, EnvFile
from envpatch.filter import (
    filter_by_pattern,
    filter_by_prefix,
    filter_secrets,
    filter_by_keys,
    FilterResult,
)


def _entry(key: str, value: str = "val", line: int = 1) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", line=line)


def _make_file(*keys: str) -> EnvFile:
    return EnvFile(entries=[_entry(k, line=i + 1) for i, k in enumerate(keys)])


def test_filter_by_pattern_matches_substring():
    env = _make_file("DB_HOST", "DB_PORT", "APP_NAME", "SECRET_KEY")
    result = filter_by_pattern(env, r"^DB_")
    assert [e.key for e in result.matched] == ["DB_HOST", "DB_PORT"]
    assert result.excluded_count == 2


def test_filter_by_pattern_no_match_returns_empty():
    env = _make_file("APP_NAME", "APP_ENV")
    result = filter_by_pattern(env, r"^DB_")
    assert result.matched == []
    assert result.excluded_count == 2


def test_filter_by_prefix_keeps_prefixed_keys():
    env = _make_file("AWS_ACCESS_KEY", "AWS_SECRET", "REDIS_URL")
    result = filter_by_prefix(env, "AWS_")
    assert [e.key for e in result.matched] == ["AWS_ACCESS_KEY", "AWS_SECRET"]


def test_filter_by_prefix_empty_prefix_matches_all():
    env = _make_file("FOO", "BAR")
    result = filter_by_prefix(env, "")
    assert result.matched_count == 2
    assert result.excluded_count == 0


def test_filter_secrets_keeps_secrets():
    env = _make_file("API_KEY", "APP_NAME", "SECRET_TOKEN", "DB_HOST")
    result = filter_secrets(env, keep_secrets=True)
    for entry in result.matched:
        assert any(word in entry.key.upper() for word in ("KEY", "SECRET", "TOKEN", "PASSWORD", "PASS"))


def test_filter_secrets_excludes_secrets():
    env = _make_file("API_KEY", "APP_NAME", "DB_HOST")
    result = filter_secrets(env, keep_secrets=False)
    for entry in result.matched:
        assert "KEY" not in entry.key.upper()


def test_filter_by_keys_explicit_list():
    env = _make_file("FOO", "BAR", "BAZ")
    result = filter_by_keys(env, ["FOO", "BAZ"])
    assert [e.key for e in result.matched] == ["FOO", "BAZ"]
    assert result.excluded_count == 1


def test_filter_by_keys_empty_list():
    env = _make_file("FOO", "BAR")
    result = filter_by_keys(env, [])
    assert result.matched == []
    assert result.excluded_count == 2


def test_as_envfile_returns_envfile_with_matched():
    env = _make_file("A", "B", "C")
    result = filter_by_keys(env, ["A", "C"])
    ef = result.as_envfile()
    assert [e.key for e in ef.entries] == ["A", "C"]


def test_summary_string():
    env = _make_file("X", "Y", "Z")
    result = filter_by_prefix(env, "X")
    assert "1 matched" in result.summary()
    assert "2 excluded" in result.summary()
