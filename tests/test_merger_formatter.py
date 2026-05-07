import pytest
from envpatch.parser import EnvEntry, EnvFile
from envpatch.merger import merge_env_files
from envpatch.merger_formatter import format_merge_report, format_merge_summary


def _entry(key, value, line=1):
    return EnvEntry(key=key, value=value, quoted=False, comment=None, line=line)


def _make_file(*entries):
    raw = "\n".join(f"{e.key}={e.value}" for e in entries if e.key)
    return EnvFile(entries=list(entries), raw=raw)


@pytest.fixture
def base_file():
    return _make_file(
        _entry("APP", "old", line=1),
        _entry("DB", "localhost", line=2),
        _entry("GONE", "bye", line=3),
    )


@pytest.fixture
def patch_file():
    return _make_file(
        _entry("APP", "new", line=1),
        _entry("DB", "localhost", line=2),
        _entry("FRESH", "hello", line=3),
    )


def test_format_report_no_changes_returns_identical_message():
    ef = _make_file(_entry("X", "1"))
    result = merge_env_files(ef, ef)
    output = format_merge_report(result, use_color=False)
    assert "identical" in output.lower() or "nothing" in output.lower()


def test_format_report_includes_added_key(base_file, patch_file):
    result = merge_env_files(base_file, patch_file)
    output = format_merge_report(result, use_color=False)
    assert "FRESH" in output
    assert "ADDED" in output


def test_format_report_includes_modified_key(base_file, patch_file):
    result = merge_env_files(base_file, patch_file)
    output = format_merge_report(result, use_color=False)
    assert "APP" in output
    assert "MODIFIED" in output


def test_format_report_includes_removed_key(base_file, patch_file):
    result = merge_env_files(base_file, patch_file)
    output = format_merge_report(result, use_color=False)
    assert "GONE" in output
    assert "REMOVED" in output


def test_format_report_skipped_hidden_by_default(base_file, patch_file):
    result = merge_env_files(base_file, patch_file, skip_keys=["DB"])
    output = format_merge_report(result, use_color=False, show_skipped=False)
    assert "DB" not in output


def test_format_report_skipped_shown_when_requested(base_file, patch_file):
    result = merge_env_files(base_file, patch_file, skip_keys=["DB"])
    output = format_merge_report(result, use_color=False, show_skipped=True)
    assert "DB" in output
    assert "SKIPPED" in output


def test_format_summary_no_changes():
    ef = _make_file(_entry("X", "1"))
    result = merge_env_files(ef, ef)
    out = format_merge_summary(result, use_color=False)
    assert "No changes" in out


def test_format_summary_with_changes(base_file, patch_file):
    result = merge_env_files(base_file, patch_file)
    out = format_merge_summary(result, use_color=False)
    assert out  # non-empty
    assert any(word in out for word in ["added", "modified", "removed"])


def test_format_report_with_color_does_not_crash(base_file, patch_file):
    result = merge_env_files(base_file, patch_file)
    output = format_merge_report(result, use_color=True)
    assert "FRESH" in output
