"""Tests for envpatch.parser — .env file parsing."""

from pathlib import Path

import pytest

from envpatch.parser import EnvFile, EnvEntry, parse_env_string, parse_env_file


SIMPLE_ENV = """
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=supersecret
"""

COMMENT_ENV = """
# This is a top-level comment
APP_ENV=production  # inline comment
DEBUG=false
"""

QUOTED_ENV = """
GREETING='hello world'
MESSAGE="goodbye cruel world"
"""


def test_parse_simple_entries():
    env = parse_env_string(SIMPLE_ENV)
    assert isinstance(env, EnvFile)
    d = env.as_dict()
    assert d["DB_HOST"] == "localhost"
    assert d["DB_PORT"] == "5432"
    assert d["SECRET_KEY"] == "supersecret"


def test_parse_ignores_blank_lines_and_comments():
    env = parse_env_string(COMMENT_ENV)
    keys = [e.key for e in env.entries]
    assert "APP_ENV" in keys
    assert "DEBUG" in keys
    assert len(keys) == 2  # top-level comment line excluded


def test_inline_comment_stripped():
    env = parse_env_string(COMMENT_ENV)
    entry = next(e for e in env.entries if e.key == "APP_ENV")
    assert entry.value == "production"
    assert entry.comment == "# inline comment"


def test_quoted_values_parsed_correctly():
    env = parse_env_string(QUOTED_ENV)
    d = env.as_dict()
    assert d["GREETING"] == "hello world"
    assert d["MESSAGE"] == "goodbye cruel world"


def test_line_numbers_recorded():
    env = parse_env_string(SIMPLE_ENV)
    assert all(e.line_number > 0 for e in env.entries)


def test_parse_env_file(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\nBAZ=qux\n", encoding="utf-8")
    result = parse_env_file(env_file)
    assert result.path == env_file
    assert result.as_dict() == {"FOO": "bar", "BAZ": "qux"}


def test_as_dict_returns_all_keys():
    env = parse_env_string(SIMPLE_ENV)
    d = env.as_dict()
    assert set(d.keys()) == {"DB_HOST", "DB_PORT", "SECRET_KEY"}
