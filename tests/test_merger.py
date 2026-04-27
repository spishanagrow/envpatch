"""Tests for envpatch.merger module."""

import pytest

from envpatch.merger import merge_env_files, MergeResult
from envpatch.parser import parse_env_string


BASE_ENV = """\
APP_NAME=myapp
DEBUG=false
DATABASE_URL=postgres://localhost/dev
SECRET_KEY=supersecret
"""

PATCH_ENV = """\
APP_NAME=myapp
DEBUG=true
DATABASE_URL=postgres://prod-host/prod
SECRET_KEY=supersecret
NEW_FEATURE_FLAG=enabled
"""


@pytest.fixture
def base_file():
    return parse_env_string(BASE_ENV)


@pytest.fixture
def patch_file():
    return parse_env_string(PATCH_ENV)


def test_merge_applies_modification(base_file, patch_file):
    result = merge_env_files(base_file, patch_file)
    output = result.as_string()
    assert "DEBUG=true" in output
    assert "DEBUG=false" not in output


def test_merge_adds_new_key(base_file, patch_file):
    result = merge_env_files(base_file, patch_file)
    assert "NEW_FEATURE_FLAG" in result.as_string()
    assert "NEW_FEATURE_FLAG" in result.applied


def test_merge_removes_key():
    base = parse_env_string("FOO=bar\nBAZ=qux\n")
    patch = parse_env_string("FOO=bar\n")
    result = merge_env_files(base, patch)
    assert "BAZ" not in result.as_string()
    assert "BAZ" in result.applied


def test_merge_skip_secrets(base_file, patch_file):
    result = merge_env_files(base_file, patch_file, skip_secrets=True)
    assert "SECRET_KEY" in result.skipped
    assert "SECRET_KEY" not in result.applied


def test_merge_result_as_string_contains_unchanged_keys(base_file, patch_file):
    result = merge_env_files(base_file, patch_file)
    assert "APP_NAME=myapp" in result.as_string()


def test_merge_preserves_key_order(base_file, patch_file):
    result = merge_env_files(base_file, patch_file)
    lines = result.lines
    app_idx = next(i for i, l in enumerate(lines) if l.startswith("APP_NAME"))
    debug_idx = next(i for i, l in enumerate(lines) if l.startswith("DEBUG"))
    assert app_idx < debug_idx


def test_merge_dry_run_returns_result(base_file, patch_file):
    result = merge_env_files(base_file, patch_file, dry_run=True)
    assert isinstance(result, MergeResult)
    assert len(result.lines) > 0


def test_merge_no_changes_returns_same_keys():
    env = parse_env_string("FOO=1\nBAR=2\n")
    result = merge_env_files(env, env)
    assert "FOO=1" in result.as_string()
    assert "BAR=2" in result.as_string()
    assert result.applied == []
