"""Tests for strategy merge formatter."""
from envpatch.parser import EnvEntry, EnvFile
from envpatch.merger_strategy import MergeStrategy, apply_strategy
from envpatch.strategy_formatter import format_strategy_report, format_strategy_summary


def _entry(key: str, value: str) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", line=1)


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


def test_format_no_conflicts_returns_ok_message():
    base = _make_file(_entry("A", "1"))
    patch = _make_file(_entry("B", "2"))
    result = apply_strategy(base, patch, MergeStrategy.THEIRS)
    output = format_strategy_report(result, color=False)
    assert "No conflicts" in output


def test_format_report_shows_overwritten_key():
    base = _make_file(_entry("DB_HOST", "localhost"))
    patch = _make_file(_entry("DB_HOST", "prod"))
    result = apply_strategy(base, patch, MergeStrategy.THEIRS)
    output = format_strategy_report(result, color=False)
    assert "DB_HOST" in output
    assert "Overwritten" in output


def test_format_report_shows_kept_key():
    base = _make_file(_entry("DB_HOST", "localhost"))
    patch = _make_file(_entry("DB_HOST", "prod"))
    result = apply_strategy(base, patch, MergeStrategy.OURS)
    output = format_strategy_report(result, color=False)
    assert "DB_HOST" in output
    assert "Kept" in output


def test_format_report_hides_overwritten_when_disabled():
    base = _make_file(_entry("KEY", "old"))
    patch = _make_file(_entry("KEY", "new"))
    result = apply_strategy(base, patch, MergeStrategy.THEIRS)
    output = format_strategy_report(result, color=False, show_overwritten=False)
    assert "Overwritten" not in output


def test_format_summary_no_conflicts():
    base = _make_file(_entry("A", "1"))
    patch = _make_file(_entry("B", "2"))
    result = apply_strategy(base, patch)
    summary = format_strategy_summary(result, color=False)
    assert summary == "no conflicts"


def test_format_summary_with_conflicts():
    base = _make_file(_entry("X", "a"))
    patch = _make_file(_entry("X", "b"))
    result = apply_strategy(base, patch, MergeStrategy.THEIRS)
    summary = format_strategy_summary(result, color=False)
    assert "overwritten" in summary
