"""CLI integration tests for the `deduplicate` subcommand."""

import pytest
from click.testing import CliRunner

from envpatch.cli import build_parser


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def clean_env(tmp_path):
    p = tmp_path / ".env"
    p.write_text("APP_NAME=myapp\nDEBUG=true\nSECRET_KEY=abc123\n")
    return str(p)


@pytest.fixture()
def dirty_env(tmp_path):
    p = tmp_path / ".env"
    p.write_text(
        "APP_NAME=first\n"
        "DEBUG=true\n"
        "APP_NAME=second\n"
        "SECRET_KEY=abc123\n"
        "DEBUG=false\n"
    )
    return str(p)


def test_deduplicate_subcommand_exists(runner):
    result = runner.invoke(build_parser(), ["deduplicate", "--help"])
    assert result.exit_code == 0


def test_deduplicate_clean_file_exits_zero(runner, clean_env):
    result = runner.invoke(build_parser(), ["deduplicate", clean_env])
    assert result.exit_code == 0


def test_deduplicate_clean_file_reports_no_duplicates(runner, clean_env):
    result = runner.invoke(build_parser(), ["deduplicate", clean_env])
    assert "No duplicate" in result.output


def test_deduplicate_dirty_file_exits_zero(runner, dirty_env):
    result = runner.invoke(build_parser(), ["deduplicate", dirty_env])
    assert result.exit_code == 0


def test_deduplicate_dirty_file_reports_removed_keys(runner, dirty_env):
    result = runner.invoke(build_parser(), ["deduplicate", dirty_env])
    assert "APP_NAME" in result.output or "DEBUG" in result.output


def test_deduplicate_keep_first_flag(runner, dirty_env):
    result = runner.invoke(
        build_parser(), ["deduplicate", "--keep", "first", dirty_env]
    )
    assert result.exit_code == 0


def test_deduplicate_write_flag_modifies_file(runner, dirty_env):
    result = runner.invoke(
        build_parser(), ["deduplicate", "--write", dirty_env]
    )
    assert result.exit_code == 0
    content = open(dirty_env).read()
    # After deduplication the key should appear only once
    assert content.count("APP_NAME=") == 1
    assert content.count("DEBUG=") == 1
