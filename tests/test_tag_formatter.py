"""Tests for envpatch.tag_formatter."""
import pytest
from envpatch.parser import EnvEntry, EnvFile
from envpatch.tagger import tag_file
from envpatch.tag_formatter import format_tag_report, format_tag_summary, format_keys_for_tag


def _entry(key: str, value: str = "val") -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=None, line_number=1, raw=f"{key}={value}")


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries), raw_lines=[])


def _result(tag_map):
    keys = list(tag_map.keys())
    f = _make_file(*[_entry(k) for k in keys])
    return tag_file(f, tag_map)


def test_format_report_no_tags_returns_message():
    f = _make_file(_entry("A"))
    result = tag_file(f, {})
    output = format_tag_report(result, use_color=False)
    assert "No tagged" in output


def test_format_report_includes_tag_name():
    result = _result({"DB_HOST": {"database"}})
    output = format_tag_report(result, use_color=False)
    assert "database" in output


def test_format_report_includes_key_name():
    result = _result({"DB_HOST": {"database"}})
    output = format_tag_report(result, use_color=False)
    assert "DB_HOST" in output


def test_format_report_lists_all_tags():
    result = _result({"A": {"x"}, "B": {"y"}})
    output = format_tag_report(result, use_color=False)
    assert "x" in output
    assert "y" in output


def test_format_report_with_color_contains_ansi():
    result = _result({"A": {"x"}})
    output = format_tag_report(result, use_color=True)
    assert "\033[" in output


def test_format_summary_contains_counts():
    result = _result({"A": {"x", "y"}, "B": {"y"}})
    summary = format_tag_summary(result, use_color=False)
    assert "tagged" in summary


def test_format_keys_for_tag_returns_keys():
    result = _result({"DB_HOST": {"db"}, "DB_PASS": {"db"}, "API_KEY": {"auth"}})
    output = format_keys_for_tag(result, "db", use_color=False)
    assert "DB_HOST" in output
    assert "DB_PASS" in output
    assert "API_KEY" not in output


def test_format_keys_for_missing_tag_returns_message():
    result = _result({"A": {"x"}})
    output = format_keys_for_tag(result, "nonexistent", use_color=False)
    assert "No keys tagged" in output
