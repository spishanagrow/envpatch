"""Tests for envpatch.filter_formatter."""

import pytest
from envpatch.parser import EnvEntry, EnvFile
from envpatch.filter import FilterResult, filter_by_prefix
from envpatch.filter_formatter import format_filter_report, format_filter_summary


def _entry(key: str, value: str = "val", line: int = 1) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", line=line)


def _make_file(*keys: str) -> EnvFile:
    return EnvFile(entries=[_entry(k, line=i + 1) for i, k in enumerate(keys)])


def test_format_empty_result_returns_no_entries_message():
    result = FilterResult(matched=[], excluded=[])
    output = format_filter_report(result)
    assert "No entries matched" in output


def test_format_report_includes_matched_keys():
    env = _make_file("DB_HOST", "DB_PORT", "APP_NAME")
    result = filter_by_prefix(env, "DB_")
    output = format_filter_report(result)
    assert "DB_HOST" in output
    assert "DB_PORT" in output
    assert "APP_NAME" not in output


def test_format_report_shows_excluded_when_requested():
    env = _make_file("DB_HOST", "APP_NAME")
    result = filter_by_prefix(env, "DB_")
    output = format_filter_report(result, show_excluded=True)
    assert "APP_NAME" in output


def test_format_report_hides_excluded_by_default():
    env = _make_file("DB_HOST", "APP_NAME")
    result = filter_by_prefix(env, "DB_")
    output = format_filter_report(result, show_excluded=False)
    assert "APP_NAME" not in output


def test_format_summary_contains_counts():
    env = _make_file("A", "B", "C")
    result = filter_by_prefix(env, "A")
    summary = format_filter_summary(result)
    assert "1" in summary
    assert "2" in summary


def test_format_report_labels_secret_keys():
    env = _make_file("API_KEY", "APP_NAME")
    result = filter_by_prefix(env, "API_")
    output = format_filter_report(result)
    assert "secret" in output.lower()
