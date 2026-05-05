"""Tests for envpatch.scoper."""
import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.scoper import ScopeResult, all_scopes, scope_file


def _entry(key: str, value: str = "val", comment: str | None = None) -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=comment, line_number=1)


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# scope_file
# ---------------------------------------------------------------------------

def test_scope_file_includes_universal_entries():
    f = _make_file(_entry("APP_NAME", "myapp"))
    result = scope_file(f, "production")
    assert any(e.key == "APP_NAME" for e in result.entries)


def test_scope_file_includes_matching_scoped_entries():
    f = _make_file(_entry("DB_HOST", "prod-db", comment="scope:production"))
    result = scope_file(f, "production")
    assert any(e.key == "DB_HOST" for e in result.matched)


def test_scope_file_excludes_other_scoped_entries():
    f = _make_file(_entry("DB_HOST", "dev-db", comment="scope:development"))
    result = scope_file(f, "production")
    assert len(result.matched) == 0
    assert any(e.key == "DB_HOST" for e in result.excluded)


def test_scope_file_case_insensitive_scope_tag():
    f = _make_file(_entry("KEY", "v", comment="scope:Production"))
    result = scope_file(f, "production")
    assert len(result.matched) == 1


def test_scope_file_case_insensitive_scope_argument():
    f = _make_file(_entry("KEY", "v", comment="scope:production"))
    result = scope_file(f, "PRODUCTION")
    assert len(result.matched) == 1


def test_scope_file_mixed_entries():
    f = _make_file(
        _entry("UNIVERSAL"),
        _entry("PROD_KEY", comment="scope:production"),
        _entry("DEV_KEY", comment="scope:development"),
    )
    result = scope_file(f, "production")
    assert len(result.universal) == 1
    assert len(result.matched) == 1
    assert len(result.excluded) == 1
    assert len(result.entries) == 2


def test_scope_file_empty_file_returns_empty_result():
    result = scope_file(EnvFile(entries=[]), "production")
    assert result.entries == []


# ---------------------------------------------------------------------------
# ScopeResult helpers
# ---------------------------------------------------------------------------

def test_summary_contains_scope_name():
    f = _make_file(_entry("K", comment="scope:staging"))
    result = scope_file(f, "staging")
    assert "staging" in result.summary()


def test_as_envfile_returns_envfile():
    from envpatch.parser import EnvFile as EF
    f = _make_file(_entry("K"))
    result = scope_file(f, "production")
    assert isinstance(result.as_envfile(), EF)


# ---------------------------------------------------------------------------
# all_scopes
# ---------------------------------------------------------------------------

def test_all_scopes_returns_unique_sorted():
    f = _make_file(
        _entry("A", comment="scope:production"),
        _entry("B", comment="scope:development"),
        _entry("C", comment="scope:production"),
    )
    assert all_scopes(f) == ["development", "production"]


def test_all_scopes_empty_when_no_tags():
    f = _make_file(_entry("A"), _entry("B"))
    assert all_scopes(f) == []
