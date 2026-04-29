"""Tests for envpatch.linter."""
import pytest

from envpatch.parser import EnvFile, EnvEntry
from envpatch.linter import (
    LintCode,
    LintIssue,
    LintReport,
    lint_file,
)


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


def _entry(key: str, value: str, line: int = 1) -> EnvEntry:
    return EnvEntry(key=key, value=value, line=line)


# ---------------------------------------------------------------------------
# LintReport helpers
# ---------------------------------------------------------------------------

def test_report_has_issues_false_when_empty():
    report = LintReport()
    assert not report.has_issues


def test_report_has_issues_true_when_populated():
    issue = LintIssue(LintCode.KEY_NOT_UPPERCASE, "foo", 1, "msg")
    report = LintReport(issues=[issue])
    assert report.has_issues


def test_report_by_code_filters_correctly():
    i1 = LintIssue(LintCode.KEY_NOT_UPPERCASE, "foo", 1, "m")
    i2 = LintIssue(LintCode.DUPLICATE_KEY, "FOO", 3, "m")
    report = LintReport(issues=[i1, i2])
    assert report.by_code(LintCode.KEY_NOT_UPPERCASE) == [i1]
    assert report.by_code(LintCode.DUPLICATE_KEY) == [i2]


def test_report_to_dict_structure():
    issue = LintIssue(LintCode.KEY_HAS_SPACES, "bad key", 2, "spaces")
    d = LintReport(issues=[issue]).to_dict()
    assert d["issue_count"] == 1
    assert d["issues"][0]["code"] == "KEY_HAS_SPACES"


# ---------------------------------------------------------------------------
# Individual lint checks
# ---------------------------------------------------------------------------

def test_lint_detects_lowercase_key():
    f = _make_file(_entry("db_host", "localhost"))
    report = lint_file(f)
    codes = [i.code for i in report.issues]
    assert LintCode.KEY_NOT_UPPERCASE in codes


def test_lint_accepts_uppercase_key():
    f = _make_file(_entry("DB_HOST", "localhost"))
    report = lint_file(f)
    assert not report.has_issues


def test_lint_detects_key_with_spaces():
    f = _make_file(_entry("MY KEY", "value"))
    report = lint_file(f)
    codes = [i.code for i in report.issues]
    assert LintCode.KEY_HAS_SPACES in codes


def test_lint_detects_trailing_space_in_value():
    f = _make_file(_entry("API_URL", "http://example.com   "))
    report = lint_file(f)
    codes = [i.code for i in report.issues]
    assert LintCode.VALUE_HAS_TRAILING_SPACE in codes


def test_lint_detects_duplicate_key():
    f = _make_file(_entry("PORT", "8080", 1), _entry("PORT", "9090", 4))
    report = lint_file(f)
    codes = [i.code for i in report.issues]
    assert LintCode.DUPLICATE_KEY in codes


def test_lint_detects_inconsistent_quotes():
    entries = [
        _entry("A", '"double"', 1),
        _entry("B", '"double"', 2),
        _entry("C", "'single'", 3),
    ]
    f = _make_file(*entries)
    report = lint_file(f)
    codes = [i.code for i in report.issues]
    assert LintCode.INCONSISTENT_QUOTE_STYLE in codes


def test_lint_no_issues_for_clean_file():
    entries = [
        _entry("DATABASE_URL", '"postgres://localhost/db"', 1),
        _entry("SECRET_KEY", '"s3cr3t"', 2),
        _entry("DEBUG", '"false"', 3),
    ]
    f = _make_file(*entries)
    report = lint_file(f)
    assert not report.has_issues


def test_lint_issue_str_representation():
    issue = LintIssue(LintCode.DUPLICATE_KEY, "PORT", 5, "Duplicate of line 1")
    s = str(issue)
    assert "DUPLICATE_KEY" in s
    assert "PORT" in s
    assert "5" in s
