"""Tests for envpatch.validator module."""

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.validator import (
    Severity,
    ValidationIssue,
    validate_env_file,
)


def _make_file(*entries: tuple) -> EnvFile:
    """Helper: build an EnvFile from (key, value, lineno) tuples."""
    env_entries = [
        EnvEntry(key=k, value=v, raw_line=f"{k}={v}", line_number=n)
        for k, v, n in entries
    ]
    return EnvFile(entries=env_entries)


def test_valid_file_produces_no_issues():
    env = _make_file(("APP_ENV", "production", 1), ("PORT", "8080", 2))
    result = validate_env_file(env)
    assert result.is_valid
    assert result.issues == []


def test_empty_required_key_is_error():
    env = _make_file(("SECRET_KEY", "", 1))
    result = validate_env_file(env)
    assert result.has_errors
    errors = [i for i in result.issues if i.severity == Severity.ERROR]
    assert len(errors) == 1
    assert errors[0].key == "SECRET_KEY"


def test_placeholder_value_is_warning():
    env = _make_file(("API_TOKEN", "changeme", 3))
    result = validate_env_file(env)
    assert result.has_warnings
    assert result.is_valid  # warnings don't make it invalid
    warnings = [i for i in result.issues if i.severity == Severity.WARNING]
    assert any("placeholder" in w.message for w in warnings)


def test_multiple_placeholder_patterns_detected():
    env = _make_file(
        ("TOKEN", "replace_me_now", 1),
        ("KEY", "<your_secret>", 2),
    )
    result = validate_env_file(env)
    warning_keys = {i.key for i in result.issues if i.severity == Severity.WARNING}
    assert "TOKEN" in warning_keys
    assert "KEY" in warning_keys


def test_empty_non_required_key_is_warning():
    env = _make_file(("OPTIONAL_FLAG", "", 5))
    result = validate_env_file(env)
    assert result.has_warnings
    assert result.is_valid
    warnings = [i for i in result.issues if i.key == "OPTIONAL_FLAG"]
    assert len(warnings) == 1
    assert "empty" in warnings[0].message


def test_issue_str_includes_line_number():
    issue = ValidationIssue(
        key="FOO", message="some problem", severity=Severity.WARNING, line_number=7
    )
    assert "line 7" in str(issue)
    assert "FOO" in str(issue)


def test_issue_str_without_line_number():
    issue = ValidationIssue(key="BAR", message="no line", severity=Severity.ERROR)
    text = str(issue)
    assert "line" not in text
    assert "BAR" in text


def test_database_url_empty_is_error():
    env = _make_file(("DATABASE_URL", "", 2))
    result = validate_env_file(env)
    assert result.has_errors
    assert not result.is_valid
