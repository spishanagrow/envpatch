"""Tests for envpatch.merger_formatter."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.merger import merge_env_files
from envpatch.merger_formatter import format_merge_report, format_merge_summary


def _entry(key: str, value: str, line: int = 1) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", line_number=line)


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries), raw_lines=[e.raw for e in entries])


@pytest.fixture()
def base_file():
    return _make_file(
        _entry("APP_NAME", "myapp", 1),
        _entry("DB_HOST", "localhost", 2),
        _entry("SECRET_KEY", "old-secret", 3),
    )


@pytest.fixture()
def patch_file():
    return _make_file(
        _entry("APP_NAME", "myapp", 1),
        _entry("DB_HOST", "prod-db", 2),
        _entry("NEW_KEY", "hello", 3),
    )


def test_format_report_no_changes_returns_identical_message(base_file):
    result = merge_env_files(base_file, base_file)
    output = format_merge_report(result)
    assert "identical" in output.lower() or "no changes" in output.lower()


def test_format_report_shows_added_key(base_file, patch_file):
    result = merge_env_files(base_file, patch_file)
    output = format_merge_report(result)
    assert "NEW_KEY" in output


def test_format_report_shows_removed_key(base_file, patch_file):
    result = merge_env_files(base_file, patch_file)
    output = format_merge_report(result)
    assert "SECRET_KEY" in output


def test_format_report_shows_modified_key(base_file, patch_file):
    result = merge_env_files(base_file, patch_file)
    output = format_merge_report(result)
    assert "DB_HOST" in output


def test_format_report_show_values_includes_value(base_file, patch_file):
    result = merge_env_files(base_file, patch_file)
    output = format_merge_report(result, show_values=True)
    assert "hello" in output


def test_format_report_hide_values_excludes_value(base_file, patch_file):
    """When show_values is False (default), sensitive values should not appear in output."""
    result = merge_env_files(base_file, patch_file)
    output = format_merge_report(result, show_values=False)
    assert "hello" not in output
    assert "prod-db" not in output
    assert "old-secret" not in output


def test_format_summary_no_changes(base_file):
    result = merge_env_files(base_file, base_file)
    summary = format_merge_summary(result)
    assert "no changes" in summary.lower()


def test_format_summary_counts_added(base_file, patch_file):
    result = merge_env_files(base_file, patch_file)
    summary = format_merge_summary(result)
    assert "added" in summary


def test_format_summary_counts_removed(base_file, patch_file):
    result = merge_env_files(base_file, patch_file)
    summary = format_merge_summary(result)
    assert "removed" in summary


def test_format_summary_counts_modified(base_file, patch_file):
    result = merge_env_files(base_file, patch_file)
    summary = format_merge_summary(result)
    assert "modified" in summary
