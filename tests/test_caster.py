"""Tests for envpatch.caster."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.caster import cast_file, _cast_value, CastResult


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _entry(key: str, value: str, line: int = 1) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", line=line)


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# _cast_value unit tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("true", True),
    ("True", True),
    ("yes", True),
    ("1", True),
    ("false", False),
    ("False", False),
    ("no", False),
    ("0", False),
])
def test_cast_value_booleans(raw, expected):
    assert _cast_value(raw) is expected


def test_cast_value_integer():
    assert _cast_value("42") == 42
    assert isinstance(_cast_value("42"), int)


def test_cast_value_float():
    result = _cast_value("3.14")
    assert isinstance(result, float)
    assert abs(result - 3.14) < 1e-9


def test_cast_value_list():
    result = _cast_value("a,b,c")
    assert result == ["a", "b", "c"]


def test_cast_value_list_strips_whitespace():
    result = _cast_value("a , b , c")
    assert result == ["a", "b", "c"]


def test_cast_value_plain_string():
    result = _cast_value("hello")
    assert result == "hello"
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# cast_file integration tests
# ---------------------------------------------------------------------------

def test_cast_file_bool_and_int():
    f = _make_file(
        _entry("DEBUG", "true", 1),
        _entry("PORT", "8080", 2),
    )
    result = cast_file(f)
    assert result.values["DEBUG"] is True
    assert result.values["PORT"] == 8080
    assert result.cast_count == 2
    assert result.plain_count == 0


def test_cast_file_plain_string_increments_plain_count():
    f = _make_file(_entry("NAME", "myapp", 1))
    result = cast_file(f)
    assert result.values["NAME"] == "myapp"
    assert result.plain_count == 1
    assert result.cast_count == 0


def test_cast_file_restricted_keys():
    f = _make_file(
        _entry("PORT", "9000", 1),
        _entry("HOST", "localhost", 2),
    )
    result = cast_file(f, keys=["PORT"])
    assert isinstance(result.values["PORT"], int)
    # HOST not in keys -> kept as raw string
    assert isinstance(result.values["HOST"], str)


def test_cast_file_types_dict_populated():
    f = _make_file(
        _entry("ENABLED", "yes", 1),
        _entry("RATIO", "0.5", 2),
        _entry("LABEL", "prod", 3),
    )
    result = cast_file(f)
    assert result.types["ENABLED"] == "bool"
    assert result.types["RATIO"] == "float"
    assert result.types["LABEL"] == "str"


def test_cast_file_to_dict_keys():
    f = _make_file(_entry("X", "1", 1))
    d = cast_file(f).to_dict()
    assert set(d.keys()) == {"values", "types", "cast_count", "plain_count"}


def test_cast_file_summary_string():
    f = _make_file(_entry("A", "true"), _entry("B", "hello"))
    result = cast_file(f)
    summary = result.summary()
    assert "2 key(s)" in summary
    assert "cast" in summary
