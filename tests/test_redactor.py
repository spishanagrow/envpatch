"""Tests for envpatch.redactor module."""

import pytest
from envpatch.parser import parse_env_string
from envpatch.redactor import (
    redact_entry,
    redact_file,
    redact_string,
    summary,
    DEFAULT_MASK,
)


SAMPLE_ENV = """\
APP_NAME=myapp
DB_PASSWORD=supersecret
API_KEY=abc123
DEBUG=true
SECRET_TOKEN=tok_xyz
"""


@pytest.fixture
def sample_file():
    return parse_env_string(SAMPLE_ENV)


def test_redact_entry_masks_secret_key(sample_file):
    secret_entry = next(e for e in sample_file.entries if e.key == "DB_PASSWORD")
    redacted = redact_entry(secret_entry)
    assert redacted.value == DEFAULT_MASK
    assert redacted.key == "DB_PASSWORD"


def test_redact_entry_leaves_plain_key(sample_file):
    plain_entry = next(e for e in sample_file.entries if e.key == "APP_NAME")
    redacted = redact_entry(plain_entry)
    assert redacted.value == "myapp"


def test_redact_entry_uses_custom_mask(sample_file):
    secret_entry = next(e for e in sample_file.entries if e.key == "API_KEY")
    redacted = redact_entry(secret_entry, mask="[hidden]")
    assert redacted.value == "[hidden]"


def test_redact_file_masks_all_secrets(sample_file):
    redacted = redact_file(sample_file)
    values = {e.key: e.value for e in redacted.entries}
    assert values["DB_PASSWORD"] == DEFAULT_MASK
    assert values["API_KEY"] == DEFAULT_MASK
    assert values["SECRET_TOKEN"] == DEFAULT_MASK
    assert values["APP_NAME"] == "myapp"
    assert values["DEBUG"] == "true"


def test_redact_file_does_not_mutate_original(sample_file):
    original_values = {e.key: e.value for e in sample_file.entries}
    redact_file(sample_file)
    for entry in sample_file.entries:
        assert entry.value == original_values[entry.key]


def test_redact_string_returns_string(sample_file):
    result = redact_string(SAMPLE_ENV)
    assert isinstance(result, str)
    assert "DB_PASSWORD=" + DEFAULT_MASK in result
    assert "APP_NAME=myapp" in result


def test_summary_counts_correctly(sample_file):
    result = summary(sample_file)
    assert result["total"] == 5
    assert result["secrets"] == 3  # DB_PASSWORD, API_KEY, SECRET_TOKEN
    assert result["plain"] == 2


def test_summary_all_plain():
    plain_env = parse_env_string("APP_NAME=foo\nDEBUG=true\n")
    result = summary(plain_env)
    assert result["secrets"] == 0
    assert result["plain"] == 2
