"""Tests for envpatch.split_formatter."""
import pytest
from envpatch.parser import EnvEntry, EnvFile
from envpatch.splitter import split_by_prefix, SplitResult
from envpatch.split_formatter import format_split_report, format_split_summary


def _entry(key: str, value: str = "val") -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=None, line_number=1, raw=f"{key}={value}")


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


def _result() -> SplitResult:
    f = _make_file(_entry("DB_HOST", "localhost"), _entry("APP_NAME", "myapp"), _entry("OTHER", "x"))
    return split_by_prefix(f, ["DB_", "APP_"])


def test_format_empty_result_returns_no_entries_message():
    result = SplitResult()
    out = format_split_report(result, use_color=False)
    assert "No entries" in out


def test_format_report_includes_bucket_name():
    out = format_split_report(_result(), use_color=False)
    assert "DB" in out
    assert "APP" in out


def test_format_report_includes_key_names():
    out = format_split_report(_result(), use_color=False)
    assert "DB_HOST" in out
    assert "APP_NAME" in out


def test_format_report_shows_unmatched_section():
    out = format_split_report(_result(), use_color=False)
    assert "unmatched" in out
    assert "OTHER" in out


def test_format_report_no_unmatched_when_all_matched():
    f = _make_file(_entry("DB_HOST"))
    result = split_by_prefix(f, ["DB_"])
    out = format_split_report(result, use_color=False)
    assert "unmatched" not in out


def test_format_summary_includes_counts():
    out = format_split_summary(_result(), use_color=False)
    assert "3" in out  # total entries
    assert "2" in out  # buckets


def test_format_summary_no_color_has_no_escape():
    out = format_split_summary(_result(), use_color=False)
    assert "\033[" not in out


def test_format_report_with_color_contains_escape():
    out = format_split_report(_result(), use_color=True)
    assert "\033[" in out
