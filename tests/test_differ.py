"""Tests for envpatch.differ and envpatch.formatter."""

import pytest

from envpatch.differ import ChangeType, diff_env_files
from envpatch.formatter import format_diff, format_summary
from envpatch.parser import parse_env_string


BASE_ENV = """
DB_HOST=localhost
DB_PORT=5432
API_KEY=old-secret
DEBUG=true
"""

TARGET_ENV = """
DB_HOST=localhost
DB_PORT=5433
API_KEY=new-secret
NEW_FEATURE=enabled
"""


@pytest.fixture
def base_file():
    return parse_env_string(BASE_ENV)


@pytest.fixture
def target_file():
    return parse_env_string(TARGET_ENV)


def test_diff_detects_added_key(base_file, target_file):
    result = diff_env_files(base_file, target_file)
    added_keys = [e.key for e in result.added()]
    assert "NEW_FEATURE" in added_keys


def test_diff_detects_removed_key(base_file, target_file):
    result = diff_env_files(base_file, target_file)
    removed_keys = [e.key for e in result.removed()]
    assert "DEBUG" in removed_keys


def test_diff_detects_modified_key(base_file, target_file):
    result = diff_env_files(base_file, target_file)
    modified_keys = [e.key for e in result.modified()]
    assert "DB_PORT" in modified_keys
    assert "API_KEY" in modified_keys


def test_unchanged_key_not_in_default_diff(base_file, target_file):
    result = diff_env_files(base_file, target_file)
    keys = [e.key for e in result.entries]
    assert "DB_HOST" not in keys


def test_unchanged_key_included_when_requested(base_file, target_file):
    result = diff_env_files(base_file, target_file, include_unchanged=True)
    unchanged = [e for e in result.entries if e.change_type == ChangeType.UNCHANGED]
    assert any(e.key == "DB_HOST" for e in unchanged)


def test_secret_values_masked_in_formatter(base_file, target_file):
    result = diff_env_files(base_file, target_file)
    output = format_diff(result, use_color=False, mask_secrets=True)
    assert "old-secret" not in output
    assert "new-secret" not in output
    assert "***" in output


def test_values_visible_when_masking_disabled(base_file, target_file):
    result = diff_env_files(base_file, target_file)
    output = format_diff(result, use_color=False, mask_secrets=False)
    assert "new-secret" in output


def test_format_summary_counts(base_file, target_file):
    result = diff_env_files(base_file, target_file)
    summary = format_summary(result)
    assert "+1 added" in summary
    assert "-1 removed" in summary
    assert "~2 modified" in summary


def test_no_diff_between_identical_files(base_file):
    result = diff_env_files(base_file, base_file)
    assert not result.has_changes()
    output = format_diff(result, use_color=False)
    assert "No differences found" in output
