"""Tests for envpatch.promoter."""
import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.promoter import PromoteResult, promote_env


def _entry(key: str, value: str, line: int = 1) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", line=line)


def _make_file(*pairs: tuple) -> EnvFile:
    return EnvFile(
        entries=[_entry(k, v, i + 1) for i, (k, v) in enumerate(pairs)]
    )


@pytest.fixture
def source_file():
    return _make_file(
        ("DB_HOST", "prod-db.example.com"),
        ("DB_PORT", "5432"),
        ("API_KEY", "secret-prod"),
    )


@pytest.fixture
def target_file():
    return _make_file(
        ("DB_HOST", "localhost"),
        ("DB_PORT", "5432"),
        ("DEBUG", "true"),
    )


def test_promote_all_keys_by_default(source_file, target_file):
    result = promote_env(source_file, target_file)
    promoted_keys = {e.key for e in result.promoted}
    assert promoted_keys == {"DB_HOST", "DB_PORT", "API_KEY"}


def test_promote_overwrites_existing_key(source_file, target_file):
    result = promote_env(source_file, target_file, overwrite=True)
    assert any(e.key == "DB_HOST" for e in result.overwritten)


def test_promote_skips_existing_when_overwrite_false(source_file, target_file):
    result = promote_env(source_file, target_file, overwrite=False)
    skipped_keys = {e.key for e in result.skipped}
    assert "DB_HOST" in skipped_keys
    assert "DB_PORT" in skipped_keys


def test_promote_new_key_not_in_overwritten(source_file, target_file):
    result = promote_env(source_file, target_file, overwrite=True)
    overwritten_keys = {e.key for e in result.overwritten}
    assert "API_KEY" not in overwritten_keys


def test_promote_with_key_allowlist(source_file, target_file):
    result = promote_env(source_file, target_file, keys=["DB_HOST"])
    promoted_keys = {e.key for e in result.promoted}
    assert promoted_keys == {"DB_HOST"}


def test_promote_keys_not_in_allowlist_are_skipped(source_file, target_file):
    result = promote_env(source_file, target_file, keys=["DB_HOST"])
    skipped_keys = {e.key for e in result.skipped}
    assert "API_KEY" in skipped_keys
    assert "DB_PORT" in skipped_keys


def test_promote_counts(source_file, target_file):
    result = promote_env(source_file, target_file, overwrite=True)
    assert result.promoted_count() == 3
    assert result.skipped_count() == 0


def test_promote_summary_contains_env_labels(source_file, target_file):
    result = promote_env(
        source_file, target_file, source_env="production", target_env="staging"
    )
    summary = result.summary()
    assert "production" in summary
    assert "staging" in summary


def test_promote_as_envfile_returns_envfile(source_file, target_file):
    result = promote_env(source_file, target_file)
    env = result.as_envfile()
    assert hasattr(env, "entries")
    assert len(env.entries) == result.promoted_count()


def test_promote_empty_source_produces_no_promoted():
    empty = EnvFile(entries=[])
    target = _make_file(("FOO", "bar"))
    result = promote_env(empty, target)
    assert result.promoted_count() == 0
