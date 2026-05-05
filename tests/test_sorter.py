"""Tests for envpatch.sorter."""

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.sorter import SortResult, sort_file


def _entry(key: str, value: str = "val", line: int = 1) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw_value=value, line=line)


def _comment(text: str, line: int = 1) -> EnvEntry:
    return EnvEntry(key=None, value=None, raw_value=None, comment=text, line=line)


def _make_file(*keys: str) -> EnvFile:
    return EnvFile(entries=[_entry(k, line=i + 1) for i, k in enumerate(keys)])


# ---------------------------------------------------------------------------
# alpha sort
# ---------------------------------------------------------------------------

def test_sort_alpha_orders_keys():
    f = _make_file("ZEBRA", "ALPHA", "MANGO")
    result = sort_file(f, mode="alpha")
    sorted_keys = [e.key for e in result.sorted_entries if e.key]
    assert sorted_keys == ["ALPHA", "MANGO", "ZEBRA"]


def test_sort_alpha_case_insensitive():
    f = _make_file("b_KEY", "A_KEY", "C_KEY")
    result = sort_file(f, mode="alpha")
    sorted_keys = [e.key for e in result.sorted_entries if e.key]
    assert sorted_keys == ["A_KEY", "b_KEY", "C_KEY"]


def test_sort_reverse():
    f = _make_file("ALPHA", "MANGO", "ZEBRA")
    result = sort_file(f, mode="alpha", reverse=True)
    sorted_keys = [e.key for e in result.sorted_entries if e.key]
    assert sorted_keys == ["ZEBRA", "MANGO", "ALPHA"]


# ---------------------------------------------------------------------------
# prefix sort
# ---------------------------------------------------------------------------

def test_sort_prefix_groups_by_prefix():
    f = _make_file("DB_PORT", "APP_NAME", "DB_HOST", "APP_ENV")
    result = sort_file(f, mode="prefix")
    sorted_keys = [e.key for e in result.sorted_entries if e.key]
    assert sorted_keys == ["APP_ENV", "APP_NAME", "DB_HOST", "DB_PORT"]


# ---------------------------------------------------------------------------
# moved_count
# ---------------------------------------------------------------------------

def test_moved_count_zero_when_already_sorted():
    f = _make_file("ALPHA", "BETA", "GAMMA")
    result = sort_file(f)
    assert result.moved_count == 0


def test_moved_count_nonzero_when_reordered():
    f = _make_file("ZEBRA", "ALPHA")
    result = sort_file(f)
    assert result.moved_count > 0


# ---------------------------------------------------------------------------
# custom key_func
# ---------------------------------------------------------------------------

def test_custom_key_func_applied():
    f = _make_file("SHORT", "VERY_LONG_KEY", "MED_KEY")
    result = sort_file(f, key_func=lambda e: len(e.key or ""))
    sorted_keys = [e.key for e in result.sorted_entries if e.key]
    assert sorted_keys == ["SHORT", "MED_KEY", "VERY_LONG_KEY"]


# ---------------------------------------------------------------------------
# comments preserved
# ---------------------------------------------------------------------------

def test_comments_preserved_at_top():
    entries = [_comment("# header", 1), _entry("ZEBRA", line=2), _entry("ALPHA", line=3)]
    f = EnvFile(entries=entries)
    result = sort_file(f)
    assert result.sorted_entries[0].comment == "# header"


# ---------------------------------------------------------------------------
# as_string / summary
# ---------------------------------------------------------------------------

def test_as_string_produces_valid_env():
    f = _make_file("BETA", "ALPHA")
    result = sort_file(f)
    text = result.as_string()
    assert "ALPHA=" in text
    assert "BETA=" in text
    assert text.index("ALPHA") < text.index("BETA")


def test_summary_already_sorted():
    f = _make_file("ALPHA", "BETA")
    result = sort_file(f)
    assert "no changes" in result.summary().lower()


def test_summary_reports_moved():
    f = _make_file("ZEBRA", "ALPHA")
    result = sort_file(f)
    assert "sorted" in result.summary().lower()
