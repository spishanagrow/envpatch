"""Tests for envpatch.trimmer."""
import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.trimmer import TrimResult, trim_file


def _entry(key: str, value: str, line_number: int = 1) -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=None, line_number=line_number, raw=f"{key}={value}")


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# trim_file – basic behaviour
# ---------------------------------------------------------------------------

def test_trim_removes_leading_spaces():
    f = _make_file(_entry("KEY", "  hello"))
    result = trim_file(f)
    assert result.entries[0].value == "hello"


def test_trim_removes_trailing_spaces():
    f = _make_file(_entry("KEY", "world   "))
    result = trim_file(f)
    assert result.entries[0].value == "world"


def test_trim_removes_both_sides():
    f = _make_file(_entry("KEY", "  both  "))
    result = trim_file(f)
    assert result.entries[0].value == "both"


def test_clean_value_not_marked_as_trimmed():
    f = _make_file(_entry("KEY", "clean"))
    result = trim_file(f)
    assert "KEY" not in result.trimmed_keys
    assert "KEY" in result.skipped_keys


def test_trimmed_key_recorded():
    f = _make_file(_entry("KEY", "  value  "))
    result = trim_file(f)
    assert "KEY" in result.trimmed_keys


def test_trim_multiple_entries():
    f = _make_file(
        _entry("A", " a ", 1),
        _entry("B", "b", 2),
        _entry("C", "  c", 3),
    )
    result = trim_file(f)
    assert result.trimmed_count() == 2
    assert result.skipped_count() == 1


def test_trim_with_keys_filter_only_trims_named_keys():
    f = _make_file(
        _entry("A", "  a  ", 1),
        _entry("B", "  b  ", 2),
    )
    result = trim_file(f, keys=["A"])
    assert result.entries[0].value == "a"
    assert result.entries[1].value == "  b  "  # untouched


def test_trim_none_value_entry_not_changed():
    entry = EnvEntry(key=None, value=None, comment="# comment", line_number=1, raw="# comment")
    f = EnvFile(entries=[entry])
    result = trim_file(f)
    assert result.entries[0].value is None
    assert result.trimmed_count() == 0


def test_as_envfile_returns_envfile():
    f = _make_file(_entry("KEY", " v "))
    result = trim_file(f)
    env = result.as_envfile()
    assert isinstance(env, EnvFile)
    assert env.entries[0].value == "v"


def test_summary_message_correct():
    f = _make_file(
        _entry("A", " a ", 1),
        _entry("B", "b", 2),
    )
    result = trim_file(f)
    assert "1" in result.summary()
    assert "1" in result.summary()
