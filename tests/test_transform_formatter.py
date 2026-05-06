"""Tests for envpatch.transform_formatter."""

from envpatch.parser import EnvEntry, EnvFile
from envpatch.transformer import TransformResult
from envpatch.transform_formatter import format_transform_report, format_transform_summary


def _result(transformed=None, skipped=None) -> TransformResult:
    return TransformResult(
        entries=[],
        transformed_keys=transformed or [],
        skipped_keys=skipped or [],
    )


def test_format_empty_result_returns_no_transform_message():
    out = format_transform_report(_result())
    assert "No keys" in out


def test_format_report_includes_transformed_key():
    out = format_transform_report(_result(transformed=["API_KEY"]))
    assert "API_KEY" in out


def test_format_report_includes_transformed_label():
    out = format_transform_report(_result(transformed=["API_KEY"]))
    assert "TRANSFORMED" in out


def test_format_report_hides_skipped_by_default():
    out = format_transform_report(_result(transformed=["A"], skipped=["B"]))
    assert "B" not in out


def test_format_report_shows_skipped_when_requested():
    out = format_transform_report(
        _result(transformed=["A"], skipped=["B"]), show_skipped=True
    )
    assert "B" in out
    assert "SKIPPED" in out


def test_format_summary_shows_counts():
    out = format_transform_summary(_result(transformed=["A", "B"], skipped=["C"]))
    assert "2" in out
    assert "1" in out


def test_format_summary_nothing_to_do_when_empty():
    out = format_transform_summary(_result())
    assert "nothing" in out
