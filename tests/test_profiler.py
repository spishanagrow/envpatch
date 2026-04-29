"""Tests for envpatch.profiler."""

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.profiler import profile_file, ProfileReport, _is_placeholder


def _make_file(entries, raw_lines=None) -> EnvFile:
    return EnvFile(
        entries=entries,
        raw_lines=raw_lines or [f"{e.key}={e.raw_value}" for e in entries],
    )


def _entry(key, value, raw_value=None, line=1) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw_value=raw_value or value, line_number=line)


# ---------------------------------------------------------------------------
# _is_placeholder helper
# ---------------------------------------------------------------------------

def test_placeholder_detects_changeme():
    assert _is_placeholder("changeme") is True


def test_placeholder_detects_angle_brackets():
    assert _is_placeholder("<your-token>") is True


def test_placeholder_ignores_real_value():
    assert _is_placeholder("s3cr3tP@ssw0rd!") is False


# ---------------------------------------------------------------------------
# profile_file
# ---------------------------------------------------------------------------

def test_profile_counts_total_keys():
    f = _make_file([_entry("FOO", "bar"), _entry("BAZ", "qux")])
    report = profile_file(f)
    assert report.total_keys == 2


def test_profile_identifies_secret_keys():
    f = _make_file([
        _entry("API_SECRET", "abc123"),
        _entry("DB_PASSWORD", "pass"),
        _entry("APP_NAME", "myapp"),
    ])
    report = profile_file(f)
    assert report.secret_keys == 2
    assert report.plain_keys == 1
    assert "API_SECRET" in report.secret_names
    assert "DB_PASSWORD" in report.secret_names


def test_profile_detects_empty_values():
    f = _make_file([_entry("EMPTY_KEY", ""), _entry("FULL_KEY", "value")])
    report = profile_file(f)
    assert report.empty_values == 1
    assert "EMPTY_KEY" in report.empty_names


def test_profile_detects_placeholder_values():
    f = _make_file([
        _entry("TOKEN", "changeme"),
        _entry("URL", "https://real.example.com"),
    ])
    report = profile_file(f)
    assert report.placeholder_values == 1
    assert "TOKEN" in report.placeholder_names


def test_profile_counts_quoted_values():
    f = _make_file([
        _entry("A", "hello", raw_value='"hello"'),
        _entry("B", "world", raw_value="world"),
    ])
    report = profile_file(f)
    assert report.quoted_values == 1


def test_profile_counts_comments():
    raw = ["# this is a comment", "FOO=bar", "# another comment", "BAZ=qux"]
    f = EnvFile(
        entries=[_entry("FOO", "bar", line=2), _entry("BAZ", "qux", line=4)],
        raw_lines=raw,
    )
    report = profile_file(f)
    assert report.comment_count == 2


def test_secret_ratio_calculation():
    f = _make_file([
        _entry("SECRET_KEY", "x"),
        _entry("PLAIN_ONE", "y"),
        _entry("PLAIN_TWO", "z"),
        _entry("PLAIN_THREE", "w"),
    ])
    report = profile_file(f)
    assert report.secret_ratio() == pytest.approx(0.25)


def test_secret_ratio_empty_file():
    f = _make_file([])
    report = profile_file(f)
    assert report.secret_ratio() == 0.0


def test_to_dict_contains_expected_keys():
    f = _make_file([_entry("FOO", "bar")])
    d = profile_file(f).to_dict()
    for key in ("total_keys", "secret_keys", "plain_keys", "empty_values",
                "placeholder_values", "quoted_values", "comment_count",
                "secret_ratio", "secret_names", "placeholder_names", "empty_names"):
        assert key in d
