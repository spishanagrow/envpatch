"""Tests for envpatch.templater."""
import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.templater import generate_template, TemplateResult, SECRET_PLACEHOLDER


def _entry(key, value, line=1):
    return EnvEntry(key=key, value=value, raw_line=f"{key}={value}", line_number=line)


def _comment(text, line=1):
    return EnvEntry(key=None, value=None, raw_line=text, line_number=line)


def _make_file(*entries):
    return EnvFile(entries=list(entries), path=".env")


# ---------------------------------------------------------------------------
# basic redaction
# ---------------------------------------------------------------------------

def test_secret_key_is_redacted():
    f = _make_file(_entry("API_SECRET", "abc123"))
    result = generate_template(f)
    entry = result.entries[0]
    assert entry.value != "abc123"
    assert "API_SECRET" in entry.value  # default uses key name


def test_non_secret_key_is_preserved():
    f = _make_file(_entry("APP_ENV", "production"))
    result = generate_template(f)
    assert result.entries[0].value == "production"


def test_redacted_count_is_correct():
    f = _make_file(
        _entry("DB_PASSWORD", "s3cr3t"),
        _entry("APP_NAME", "myapp"),
        _entry("AUTH_TOKEN", "tok"),
    )
    result = generate_template(f)
    assert result.redacted == 2
    assert result.total == 3


# ---------------------------------------------------------------------------
# placeholder variants
# ---------------------------------------------------------------------------

def test_custom_placeholder_overrides_default():
    f = _make_file(_entry("DB_PASSWORD", "s3cr3t"))
    result = generate_template(f, placeholder="CHANGEME")
    assert result.entries[0].value == "CHANGEME"


def test_use_key_name_false_uses_generic_placeholder():
    f = _make_file(_entry("API_KEY", "xyz"))
    result = generate_template(f, use_key_name=False)
    assert result.entries[0].value == SECRET_PLACEHOLDER


def test_keep_non_secrets_false_blanks_plain_values():
    f = _make_file(_entry("APP_ENV", "production"))
    result = generate_template(f, keep_non_secrets=False)
    assert result.entries[0].value == ""


# ---------------------------------------------------------------------------
# structure preservation
# ---------------------------------------------------------------------------

def test_comments_and_blanks_preserved():
    f = _make_file(
        _comment("# Database settings"),
        _entry("DB_PASSWORD", "s3cr3t"),
        _comment(""),
    )
    result = generate_template(f)
    assert result.entries[0].raw_line == "# Database settings"
    assert result.entries[2].raw_line == ""


def test_as_string_renders_key_value_pairs():
    f = _make_file(_entry("APP_ENV", "staging"), _entry("DB_PASSWORD", "x"))
    result = generate_template(f)
    output = result.as_string()
    assert "APP_ENV=staging" in output
    assert "DB_PASSWORD=" in output
    assert "x" not in output  # secret replaced


def test_summary_contains_counts():
    f = _make_file(_entry("DB_PASSWORD", "s"), _entry("APP_NAME", "app"))
    result = generate_template(f)
    assert "2 keys" in result.summary
    assert "1 redacted" in result.summary


def test_source_path_stored():
    f = _make_file(_entry("APP_ENV", "dev"))
    f.path = "/project/.env"
    result = generate_template(f)
    assert result.source_path == "/project/.env"
