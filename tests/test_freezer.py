"""Tests for envpatch.freezer."""
import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.freezer import (
    FreezeResult,
    freeze_file,
    is_frozen,
    _FREEZE_MARKER,
)


def _entry(key: str, value: str = "val", comment: str = "") -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=comment, line_number=1, raw="")


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


def test_is_frozen_returns_false_for_plain_entry():
    e = _entry("KEY")
    assert is_frozen(e) is False


def test_is_frozen_returns_true_after_marker_present():
    e = _entry("KEY", comment=_FREEZE_MARKER)
    assert is_frozen(e) is True


def test_is_frozen_detects_marker_within_longer_comment():
    e = _entry("KEY", comment=f"some note {_FREEZE_MARKER} extra")
    assert is_frozen(e) is True


def test_freeze_file_marks_all_entries_by_default():
    f = _make_file(_entry("A"), _entry("B"))
    result = freeze_file(f)
    assert result.frozen_count == 2
    assert all(is_frozen(e) for e in result.frozen)


def test_freeze_file_with_keys_filter_freezes_only_listed():
    f = _make_file(_entry("A"), _entry("B"), _entry("C"))
    result = freeze_file(f, keys=["B"])
    assert result.frozen_count == 1
    assert result.frozen[0].key == "B"
    assert len(result.skipped) == 2


def test_freeze_file_skips_already_frozen_entries():
    f = _make_file(_entry("A", comment=_FREEZE_MARKER), _entry("B"))
    result = freeze_file(f)
    assert result.already_frozen_count == 1
    assert result.frozen_count == 1


def test_freeze_file_preserves_existing_comment():
    f = _make_file(_entry("A", comment="keep this"))
    result = freeze_file(f)
    assert "keep this" in result.frozen[0].comment
    assert _FREEZE_MARKER in result.frozen[0].comment


def test_freeze_file_as_envfile_contains_all_entries():
    f = _make_file(_entry("A"), _entry("B"))
    result = freeze_file(f)
    env = result.as_envfile()
    assert len(env.entries) == 2


def test_freeze_result_summary_format():
    f = _make_file(_entry("A"), _entry("B"))
    result = freeze_file(f)
    s = result.summary()
    assert "frozen=" in s
    assert "skipped=" in s


def test_freeze_file_none_key_entries_passed_through():
    blank = EnvEntry(key=None, value=None, comment="# header", line_number=1, raw="# header")
    f = EnvFile(entries=[blank, _entry("A")])
    result = freeze_file(f)
    assert result.entries[0].key is None
    assert result.frozen_count == 1
