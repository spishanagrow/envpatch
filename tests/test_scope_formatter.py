"""Tests for envpatch.scope_formatter."""
import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.scope_formatter import (
    format_all_scopes,
    format_scope_report,
    format_scope_summary,
)
from envpatch.scoper import ScopeResult, all_scopes, scope_file


def _entry(key: str, value: str = "val", comment: str | None = None) -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=comment, line_number=1)


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# format_scope_report
# ---------------------------------------------------------------------------

def test_format_empty_result_returns_no_entries_message():
    result = scope_file(EnvFile(entries=[]), "production")
    output = format_scope_report(result)
    assert "No entries" in output


def test_format_report_includes_scope_name():
    f = _make_file(_entry("K", comment="scope:staging"))
    result = scope_file(f, "staging")
    output = format_scope_report(result)
    assert "staging" in output


def test_format_report_includes_matched_key():
    f = _make_file(_entry("DB_URL", "postgres", comment="scope:production"))
    result = scope_file(f, "production")
    output = format_scope_report(result)
    assert "DB_URL" in output


def test_format_report_includes_universal_key():
    f = _make_file(_entry("APP_NAME", "myapp"))
    result = scope_file(f, "production")
    output = format_scope_report(result)
    assert "APP_NAME" in output


def test_format_report_excluded_hidden_by_default():
    f = _make_file(_entry("DEV_KEY", comment="scope:development"))
    result = scope_file(f, "production")
    output = format_scope_report(result)
    assert "DEV_KEY" not in output


def test_format_report_excluded_shown_when_requested():
    f = _make_file(_entry("DEV_KEY", comment="scope:development"))
    result = scope_file(f, "production")
    output = format_scope_report(result, show_excluded=True)
    assert "DEV_KEY" in output


# ---------------------------------------------------------------------------
# format_scope_summary
# ---------------------------------------------------------------------------

def test_format_scope_summary_returns_string():
    f = _make_file(_entry("K"))
    result = scope_file(f, "production")
    summary = format_scope_summary(result)
    assert isinstance(summary, str)
    assert len(summary) > 0


# ---------------------------------------------------------------------------
# format_all_scopes
# ---------------------------------------------------------------------------

def test_format_all_scopes_lists_scope_names():
    f = _make_file(
        _entry("A", comment="scope:production"),
        _entry("B", comment="scope:development"),
    )
    output = format_all_scopes(all_scopes(f))
    assert "production" in output
    assert "development" in output


def test_format_all_scopes_empty_returns_message():
    output = format_all_scopes([])
    assert "No scopes" in output
