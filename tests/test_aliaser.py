"""Tests for envpatch.aliaser."""
import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.aliaser import AliasResult, alias_file, reverse_alias_map


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _entry(key: str, value: str, line: int = 1) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", line=line)


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries), raw="")


# ---------------------------------------------------------------------------
# alias_file
# ---------------------------------------------------------------------------

def test_alias_resolves_known_key():
    env = _make_file(_entry("DATABASE_PASSWORD", "s3cr3t"))
    result = alias_file(env, {"db_pass": "DATABASE_PASSWORD"})
    assert result.value_for_alias("db_pass") == "s3cr3t"


def test_alias_unresolved_when_key_missing():
    env = _make_file(_entry("APP_PORT", "8080"))
    result = alias_file(env, {"db_pass": "DATABASE_PASSWORD"})
    assert "db_pass" in result.unresolved
    assert result.value_for_alias("db_pass") is None


def test_alias_multiple_aliases():
    env = _make_file(
        _entry("DB_HOST", "localhost"),
        _entry("DB_PORT", "5432"),
    )
    result = alias_file(env, {"host": "DB_HOST", "port": "DB_PORT"})
    assert result.value_for_alias("host") == "localhost"
    assert result.value_for_alias("port") == "5432"
    assert result.unresolved == []


def test_alias_partial_resolution():
    env = _make_file(_entry("DB_HOST", "localhost"))
    result = alias_file(env, {"host": "DB_HOST", "port": "DB_PORT"})
    assert len(result.resolved) == 1
    assert len(result.unresolved) == 1


def test_keys_for_alias_returns_original_key():
    env = _make_file(_entry("SECRET_KEY", "abc"))
    result = alias_file(env, {"secret": "SECRET_KEY"})
    assert result.keys_for_alias("secret") == "SECRET_KEY"


def test_keys_for_alias_returns_none_for_unknown():
    env = _make_file(_entry("SECRET_KEY", "abc"))
    result = alias_file(env, {"secret": "SECRET_KEY"})
    assert result.keys_for_alias("nope") is None


def test_summary_all_resolved():
    env = _make_file(_entry("A", "1"), _entry("B", "2"))
    result = alias_file(env, {"a": "A", "b": "B"})
    assert result.summary() == "2/2 aliases resolved"


def test_summary_with_unresolved():
    env = _make_file(_entry("A", "1"))
    result = alias_file(env, {"a": "A", "b": "MISSING"})
    assert "1/2" in result.summary()
    assert "MISSING" not in result.summary()  # summary lists alias names
    assert "b" in result.summary()


def test_empty_alias_map():
    env = _make_file(_entry("X", "y"))
    result = alias_file(env, {})
    assert result.resolved == {}
    assert result.unresolved == []


# ---------------------------------------------------------------------------
# reverse_alias_map
# ---------------------------------------------------------------------------

def test_reverse_single_alias():
    rev = reverse_alias_map({"db_pass": "DATABASE_PASSWORD"})
    assert rev == {"DATABASE_PASSWORD": ["db_pass"]}


def test_reverse_multiple_aliases_same_key():
    rev = reverse_alias_map({"pw": "DB_PASS", "password": "DB_PASS"})
    assert set(rev["DB_PASS"]) == {"pw", "password"}


def test_reverse_empty_map():
    assert reverse_alias_map({}) == {}
