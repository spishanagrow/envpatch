"""Tests for envpatch.masker."""
import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.masker import DEFAULT_MASK, MaskResult, mask_file


def _entry(key: str, value: str, line: int = 1) -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=None, line_number=line)


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# mask_file — secrets_only (default)
# ---------------------------------------------------------------------------

def test_mask_file_masks_secret_keys_by_default():
    f = _make_file(
        _entry("API_KEY", "abc123"),
        _entry("APP_NAME", "myapp"),
    )
    result = mask_file(f)
    values = {e.key: e.value for e in result.entries if e.key}
    assert values["API_KEY"] == DEFAULT_MASK
    assert values["APP_NAME"] == "myapp"


def test_mask_file_populates_masked_and_plain_lists():
    f = _make_file(
        _entry("SECRET_TOKEN", "s3cr3t"),
        _entry("HOST", "localhost"),
    )
    result = mask_file(f)
    assert "SECRET_TOKEN" in result.masked_keys
    assert "HOST" in result.plain_keys


def test_mask_file_secrets_only_false_masks_nothing_extra():
    """With secrets_only=False and no explicit keys, nothing is masked."""
    f = _make_file(
        _entry("API_KEY", "abc123"),
        _entry("APP_NAME", "myapp"),
    )
    result = mask_file(f, secrets_only=False)
    assert result.masked_count() == 0
    assert result.plain_count() == 2


# ---------------------------------------------------------------------------
# mask_file — explicit keys
# ---------------------------------------------------------------------------

def test_mask_file_explicit_keys_overrides_secret_detection():
    f = _make_file(
        _entry("API_KEY", "abc123"),
        _entry("APP_NAME", "myapp"),
    )
    result = mask_file(f, keys={"APP_NAME"})
    values = {e.key: e.value for e in result.entries if e.key}
    # APP_NAME is explicit — must be masked
    assert values["APP_NAME"] == DEFAULT_MASK
    # API_KEY is NOT in explicit set — left as-is regardless of name
    assert values["API_KEY"] == "abc123"


def test_mask_file_unknown_explicit_key_is_ignored_gracefully():
    f = _make_file(_entry("HOST", "localhost"))
    result = mask_file(f, keys={"NONEXISTENT"})
    assert result.masked_count() == 0
    assert result.plain_count() == 1


# ---------------------------------------------------------------------------
# mask_file — custom mask string
# ---------------------------------------------------------------------------

def test_mask_file_custom_mask_string():
    f = _make_file(_entry("DB_PASSWORD", "hunter2"))
    result = mask_file(f, mask="[REDACTED]")
    assert result.entries[0].value == "[REDACTED]"


# ---------------------------------------------------------------------------
# MaskResult helpers
# ---------------------------------------------------------------------------

def test_masked_count_and_plain_count():
    f = _make_file(
        _entry("TOKEN", "t"),
        _entry("PORT", "8080"),
        _entry("DB_SECRET", "x"),
    )
    result = mask_file(f)
    assert result.masked_count() + result.plain_count() == 3


def test_summary_contains_counts():
    f = _make_file(
        _entry("API_KEY", "abc"),
        _entry("APP_ENV", "prod"),
    )
    result = mask_file(f)
    s = result.summary()
    assert "masked" in s
    assert "plain" in s


def test_as_envfile_returns_envfile_instance():
    f = _make_file(_entry("API_KEY", "abc"))
    result = mask_file(f)
    ef = result.as_envfile()
    assert isinstance(ef, EnvFile)
    assert len(ef.entries) == 1
