"""Tests for envpatch.differ_formatter."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.differ import diff_env_files, ChangeType
from envpatch.differ_formatter import (
    format_diff_entry,
    format_diff_report,
    format_diff_stats,
)


def _entry(key: str, value: str, line: int = 1) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", line_number=line)


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries), raw_lines=[e.raw for e in entries])


@pytest.fixture()
def base():
    return _make_file(
        _entry("APP_ENV", "development", 1),
        _entry("SECRET_TOKEN", "abc123", 2),
        _entry("OLD_KEY", "gone", 3),
    )


@pytest.fixture()
def target():
    return _make_file(
        _entry("APP_ENV", "production", 1),
        _entry("SECRET_TOKEN", "abc123", 2),
        _entry("NEW_KEY", "arrived", 3),
    )


def test_format_diff_entry_added_contains_plus(base, target):
    entries = diff_env_files(base, target)
    added = next(e for e in entries if e.change_type == ChangeType.ADDED)
    line = format_diff_entry(added)
    assert "+" in line
    assert added.key in line


def test_format_diff_entry_removed_contains_minus(base, target):
    entries = diff_env_files(base, target)
    removed = next(e for e in entries if e.change_type == ChangeType.REMOVED)
    line = format_diff_entry(removed)
    assert "-" in line
    assert removed.key in line


def test_format_diff_entry_modified_contains_tilde(base, target):
    entries = diff_env_files(base, target)
    modified = next(e for e in entries if e.change_type == ChangeType.MODIFIED)
    line = format_diff_entry(modified)
    assert "~" in line


def test_format_diff_entry_show_values_includes_value(base, target):
    entries = diff_env_files(base, target)
    added = next(e for e in entries if e.change_type == ChangeType.ADDED)
    line = format_diff_entry(added, show_values=True)
    assert "=" in line or "->" in line


def test_format_diff_report_no_diffs_returns_message():
    f = _make_file(_entry("X", "1"))
    entries = diff_env_files(f, f)
    output = format_diff_report(entries)
    assert "no differences" in output.lower()


def test_format_diff_report_includes_changed_keys(base, target):
    entries = diff_env_files(base, target)
    output = format_diff_report(entries)
    assert "APP_ENV" in output
    assert "NEW_KEY" in output
    assert "OLD_KEY" in output


def test_format_diff_report_excludes_unchanged_by_default(base, target):
    entries = diff_env_files(base, target)
    output = format_diff_report(entries)
    assert "SECRET_TOKEN" not in output


def test_format_diff_report_includes_unchanged_when_requested(base, target):
    entries = diff_env_files(base, target)
    output = format_diff_report(entries, show_unchanged=True)
    assert "SECRET_TOKEN" in output


def test_format_diff_stats_shows_counts(base, target):
    entries = diff_env_files(base, target)
    stats = format_diff_stats(entries)
    assert "+" in stats or "-" in stats or "~" in stats


def test_format_diff_stats_no_changes_returns_zero():
    f = _make_file(_entry("A", "1"))
    entries = diff_env_files(f, f)
    stats = format_diff_stats(entries)
    assert "0" in stats
