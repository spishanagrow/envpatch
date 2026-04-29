"""Tests for envpatch.interpolator."""

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.interpolator import interpolate_file, find_unresolved, _resolve_value


def _make_file(*pairs) -> EnvFile:
    entries = [
        EnvEntry(key=k, value=v, line_number=i + 1, raw=f"{k}={v}")
        for i, (k, v) in enumerate(pairs)
    ]
    return EnvFile(entries=entries, path="test.env")


def test_resolve_simple_reference():
    context = {"HOST": "localhost", "PORT": "5432"}
    result = _resolve_value("${HOST}:${PORT}", context)
    assert result == "localhost:5432"


def test_resolve_bare_dollar_syntax():
    context = {"NAME": "world"}
    result = _resolve_value("hello $NAME", context)
    assert result == "hello world"


def test_resolve_unknown_variable_left_as_is():
    result = _resolve_value("${UNKNOWN}", {})
    assert result == "${UNKNOWN}"


def test_resolve_circular_reference_raises():
    context = {"A": "${B}", "B": "${A}"}
    with pytest.raises(ValueError, match="Circular reference"):
        _resolve_value("${A}", context)


def test_interpolate_file_resolves_chain():
    env = _make_file(
        ("BASE_URL", "http://localhost"),
        ("API_URL", "${BASE_URL}/api"),
    )
    result = interpolate_file(env)
    assert result["API_URL"] == "http://localhost/api"
    assert result["BASE_URL"] == "http://localhost"


def test_interpolate_file_extra_context_overrides():
    env = _make_file(
        ("HOST", "localhost"),
        ("DSN", "postgres://${HOST}/db"),
    )
    result = interpolate_file(env, extra_context={"HOST": "prod.example.com"})
    assert result["DSN"] == "postgres://prod.example.com/db"


def test_interpolate_file_no_references_unchanged():
    env = _make_file(("KEY", "plain_value"), ("OTHER", "123"))
    result = interpolate_file(env)
    assert result == {"KEY": "plain_value", "OTHER": "123"}


def test_find_unresolved_returns_missing_vars():
    env = _make_file(
        ("URL", "${SCHEME}://${HOST}"),
        ("HOST", "localhost"),
    )
    unresolved = find_unresolved(env)
    assert "URL" in unresolved
    assert "SCHEME" in unresolved["URL"]
    assert "HOST" not in unresolved.get("URL", [])


def test_find_unresolved_empty_when_all_defined():
    env = _make_file(
        ("HOST", "localhost"),
        ("URL", "http://${HOST}"),
    )
    assert find_unresolved(env) == {}


def test_find_unresolved_ignores_keys_with_no_refs():
    env = _make_file(("PLAIN", "no_refs_here"))
    assert find_unresolved(env) == {}
