"""Tests for envpatch.lint_formatter."""
from envpatch.linter import LintCode, LintIssue, LintReport
from envpatch.lint_formatter import format_lint_report, format_lint_summary


def _issue(code: LintCode = LintCode.DUPLICATE_KEY, key: str = "PORT", line: int = 3) -> LintIssue:
    return LintIssue(code=code, key=key, line=line, message="test message")


# ---------------------------------------------------------------------------
# format_lint_report
# ---------------------------------------------------------------------------

def test_format_clean_report_returns_ok_message():
    report = LintReport()
    result = format_lint_report(report, use_color=False)
    assert "No lint issues" in result


def test_format_report_includes_issue_count():
    report = LintReport(issues=[_issue(), _issue(LintCode.KEY_NOT_UPPERCASE, "foo", 5)])
    result = format_lint_report(report, use_color=False)
    assert "2" in result


def test_format_report_includes_code():
    report = LintReport(issues=[_issue(LintCode.KEY_NOT_UPPERCASE, "db_host", 1)])
    result = format_lint_report(report, use_color=False)
    assert "KEY_NOT_UPPERCASE" in result


def test_format_report_includes_line_number():
    report = LintReport(issues=[_issue(line=42)])
    result = format_lint_report(report, use_color=False)
    assert "42" in result


def test_format_report_includes_key():
    report = LintReport(issues=[_issue(key="MY_VAR")])
    result = format_lint_report(report, use_color=False)
    assert "MY_VAR" in result


def test_format_report_with_color_does_not_crash():
    report = LintReport(issues=[_issue()])
    result = format_lint_report(report, use_color=True)
    assert "DUPLICATE_KEY" in result


# ---------------------------------------------------------------------------
# format_lint_summary
# ---------------------------------------------------------------------------

def test_summary_ok_when_no_issues():
    report = LintReport()
    result = format_lint_summary(report, use_color=False)
    assert result == "lint: OK"


def test_summary_shows_count_when_issues_present():
    report = LintReport(issues=[_issue(), _issue(LintCode.KEY_NOT_UPPERCASE, "x", 2)])
    result = format_lint_summary(report, use_color=False)
    assert "2" in result
    assert "issue" in result


def test_summary_with_color_does_not_crash():
    report = LintReport(issues=[_issue()])
    result = format_lint_summary(report, use_color=True)
    assert len(result) > 0
