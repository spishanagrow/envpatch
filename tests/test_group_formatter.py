"""Tests for envpatch.group_formatter."""
import pytest
from envpatch.parser import EnvEntry, EnvFile
from envpatch.grouper import GroupResult, group_by_prefix, group_by_map
from envpatch.group_formatter import format_group_report, format_group_summary


def _entry(key: str, value: str = "val") -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", line_number=1)


def _make_file(*keys: str) -> EnvFile:
    return EnvFile(entries=[_entry(k) for k in keys], raw="")


def _result(*keys: str) -> GroupResult:
    return group_by_prefix(_make_file(*keys))


def test_format_empty_result_returns_message():
    result = GroupResult()
    out = format_group_report(result, use_color=False)
    assert "No entries" in out


def test_format_report_includes_group_name():
    result = _result("DB_HOST", "DB_PORT")
    out = format_group_report(result, use_color=False)
    assert "[DB]" in out


def test_format_report_includes_key_names():
    result = _result("DB_HOST", "DB_PORT")
    out = format_group_report(result, use_color=False)
    assert "DB_HOST" in out
    assert "DB_PORT" in out


def test_format_report_shows_ungrouped_section():
    result = _result("PLAIN")
    out = format_group_report(result, use_color=False)
    assert "ungrouped" in out
    assert "PLAIN" in out


def test_format_report_groups_before_ungrouped():
    result = _result("DB_HOST", "PLAIN")
    out = format_group_report(result, use_color=False)
    db_pos = out.index("[DB]")
    ug_pos = out.index("[ungrouped]")
    assert db_pos < ug_pos


def test_format_summary_contains_group_count():
    result = _result("DB_HOST", "APP_NAME")
    out = format_group_summary(result, use_color=False)
    assert "2 group(s)" in out


def test_format_summary_contains_ungrouped_count():
    result = _result("PLAIN")
    out = format_group_summary(result, use_color=False)
    assert "1 ungrouped" in out


def test_format_with_color_contains_ansi():
    result = _result("DB_HOST")
    out = format_group_report(result, use_color=True)
    assert "\033[" in out
