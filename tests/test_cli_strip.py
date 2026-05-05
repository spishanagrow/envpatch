"""CLI integration tests for the `strip` subcommand."""

import pytest
from click.testing import CliRunner

from envpatch.cli import build_parser


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(
        "DB_HOST=localhost\n"
        "DB_PASS=supersecret\n"
        "APP_PORT=8080\n"
        "AWS_SECRET_KEY=abc123\n"
    )
    return str(p)


def test_strip_subcommand_exists(runner):
    cli = build_parser()
    result = runner.invoke(cli, ["strip", "--help"])
    assert result.exit_code == 0


def test_strip_exits_zero_on_success(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["strip", env_file, "--key", "DB_PASS"])
    assert result.exit_code == 0


def test_strip_removes_named_key_from_output(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["strip", env_file, "--key", "DB_PASS"])
    assert "DB_PASS" not in result.output
    assert "DB_HOST" in result.output


def test_strip_by_prefix_removes_matching_keys(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["strip", env_file, "--prefix", "DB_"])
    assert "DB_HOST" not in result.output
    assert "DB_PASS" not in result.output
    assert "APP_PORT" in result.output


def test_strip_by_pattern_removes_matching_keys(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["strip", env_file, "--pattern", "SECRET"])
    assert "AWS_SECRET_KEY" not in result.output
    assert "APP_PORT" in result.output


def test_strip_reports_summary(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["strip", env_file, "--key", "DB_PASS"])
    # Summary line should mention at least one stripped key
    assert "Stripped" in result.output or "stripped" in result.output
