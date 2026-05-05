"""CLI integration tests for the `filter` subcommand."""

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
        "DB_PORT=5432\n"
        "APP_NAME=myapp\n"
        "SECRET_KEY=supersecret\n"
    )
    return str(p)


def test_filter_subcommand_exists(runner):
    cli = build_parser()
    result = runner.invoke(cli, ["filter", "--help"])
    assert result.exit_code == 0


def test_filter_by_prefix_exits_zero(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["filter", env_file, "--prefix", "DB_"])
    assert result.exit_code == 0


def test_filter_by_prefix_output_contains_matched_keys(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["filter", env_file, "--prefix", "DB_"])
    assert "DB_HOST" in result.output
    assert "DB_PORT" in result.output


def test_filter_by_prefix_excludes_non_matching(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["filter", env_file, "--prefix", "DB_"])
    assert "APP_NAME" not in result.output


def test_filter_by_pattern_flag(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["filter", env_file, "--pattern", r"^APP_"])
    assert result.exit_code == 0
    assert "APP_NAME" in result.output


def test_filter_secrets_only_flag(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["filter", env_file, "--secrets-only"])
    assert result.exit_code == 0
    assert "SECRET_KEY" in result.output
