"""Tests for strategy-based merge."""
import pytest
from envpatch.parser import EnvEntry, EnvFile
from envpatch.merger_strategy import MergeStrategy, apply_strategy


def _entry(key: str, value: str, line: int = 1) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", line=line)


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


@pytest.fixture
def base():
    return _make_file(
        _entry("DB_HOST", "localhost", line=1),
        _entry("DB_PORT", "5432", line=2),
        _entry("APP_ENV", "development", line=3),
    )


@pytest.fixture
def patch():
    return _make_file(
        _entry("DB_HOST", "prod-db.internal", line=1),
        _entry("SECRET_KEY", "abc123", line=2),
    )


def test_strategy_theirs_overwrites_conflict(base, patch):
    result = apply_strategy(base, patch, MergeStrategy.THEIRS)
    mapping = {e.key: e.value for e in result.entries if e.key}
    assert mapping["DB_HOST"] == "prod-db.internal"


def test_strategy_ours_keeps_base_value(base, patch):
    result = apply_strategy(base, patch, MergeStrategy.OURS)
    mapping = {e.key: e.value for e in result.entries if e.key}
    assert mapping["DB_HOST"] == "localhost"


def test_strategy_adds_new_keys_from_patch(base, patch):
    result = apply_strategy(base, patch, MergeStrategy.THEIRS)
    keys = [e.key for e in result.entries if e.key]
    assert "SECRET_KEY" in keys


def test_strategy_preserves_base_only_keys(base, patch):
    result = apply_strategy(base, patch, MergeStrategy.THEIRS)
    keys = [e.key for e in result.entries if e.key]
    assert "DB_PORT" in keys
    assert "APP_ENV" in keys


def test_strategy_newer_prefers_higher_line_number():
    base_file = _make_file(_entry("KEY", "old", line=10))
    patch_file = _make_file(_entry("KEY", "new", line=20))
    result = apply_strategy(base_file, patch_file, MergeStrategy.NEWER)
    mapping = {e.key: e.value for e in result.entries if e.key}
    assert mapping["KEY"] == "new"
    assert "KEY" in result.overwritten


def test_strategy_newer_keeps_base_when_base_line_higher():
    base_file = _make_file(_entry("KEY", "old", line=30))
    patch_file = _make_file(_entry("KEY", "new", line=5))
    result = apply_strategy(base_file, patch_file, MergeStrategy.NEWER)
    mapping = {e.key: e.value for e in result.entries if e.key}
    assert mapping["KEY"] == "old"
    assert "KEY" in result.kept


def test_resolved_list_contains_conflict_keys(base, patch):
    result = apply_strategy(base, patch, MergeStrategy.THEIRS)
    assert "DB_HOST" in result.resolved


def test_no_conflicts_produces_empty_resolved():
    base_file = _make_file(_entry("A", "1"))
    patch_file = _make_file(_entry("B", "2"))
    result = apply_strategy(base_file, patch_file, MergeStrategy.THEIRS)
    assert result.resolved == []


def test_summary_no_conflicts():
    base_file = _make_file(_entry("A", "1"))
    patch_file = _make_file(_entry("B", "2"))
    result = apply_strategy(base_file, patch_file)
    assert result.summary() == "no conflicts"


def test_as_envfile_returns_envfile(base, patch):
    result = apply_strategy(base, patch, MergeStrategy.THEIRS)
    ef = result.as_envfile()
    assert hasattr(ef, "entries")
