"""CLI integration tests for the `transform` sub-command."""

import pytest
from click.testing import CliRunner

from envpatch.cli import build_parser


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("APP_NAME=myapp\nSECRET_KEY=abc123\nDB_HOST=localhost\n")
    return str(p)


def test_transform_subcommand_exists(runner):
    cli = build_parser()
    result = runner.invoke(cli, ["transform", "--help"])
    assert result.exit_code == 0


def test_transform_exits_zero_on_valid_file(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["transform", env_file, "--fn", "upper"])
    assert result.exit_code == 0


def test_transform_output_contains_uppercased_value(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["transform", env_file, "--fn", "upper"])
    assert "MYAPP" in result.output or "TRANSFORMED" in result.output


def test_transform_with_keys_filter(runner, env_file):
    cli = build_parser()
    result = runner.invoke(
        cli, ["transform", env_file, "--fn", "upper", "--key", "APP_NAME"]
    )
    assert result.exit_code == 0


def test_transform_unknown_fn_exits_nonzero(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["transform", env_file, "--fn", "rot99"])
    assert result.exit_code != 0
