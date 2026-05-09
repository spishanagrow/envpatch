"""Tests for envpatch.freeze_formatter."""
from envpatch.parser import EnvEntry, EnvFile
from envpatch.freezer import freeze_file, _FREEZE_MARKER
from envpatch.freeze_formatter import format_freeze_report, format_freeze_summary


def _entry(key: str, value: str = "val", comment: str = "") -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=comment, line_number=1, raw="")


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


def test_format_empty_result_returns_no_entries_message():
    f = _make_file()
    result = freeze_file(f)
    report = format_freeze_report(result, color=False)
    assert "No entries" in report


def test_format_report_includes_frozen_label():
    f = _make_file(_entry("SECRET_KEY"))
    result = freeze_file(f)
    report = format_freeze_report(result, color=False)
    assert "[frozen]" in report
    assert "SECRET_KEY" in report


def test_format_report_includes_already_frozen_label():
    f = _make_file(_entry("A", comment=_FREEZE_MARKER))
    result = freeze_file(f)
    report = format_freeze_report(result, color=False)
    assert "[already frozen]" in report


def test_format_report_includes_skipped_label():
    f = _make_file(_entry("A"), _entry("B"))
    result = freeze_file(f, keys=["A"])
    report = format_freeze_report(result, color=False)
    assert "[skipped]" in report


def test_format_summary_contains_counts():
    f = _make_file(_entry("A"), _entry("B", comment=_FREEZE_MARKER))
    result = freeze_file(f)
    summary = format_freeze_summary(result, color=False)
    assert "frozen=1" in summary
    assert "already_frozen=1" in summary


def test_format_report_header_present():
    f = _make_file(_entry("X"))
    result = freeze_file(f)
    report = format_freeze_report(result, color=False)
    assert "Freeze report" in report
