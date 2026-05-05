"""CLI integration tests for the ``sort`` subcommand."""

import pytest
from click.testing import CliRunner

from envpatch.cli import build_parser


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("ZEBRA=1\nAPPLE=2\nMANGO=3\n")
    return str(p)


def test_sort_subcommand_exists(runner):
    cli = build_parser()
    result = runner.invoke(cli, ["sort", "--help"])
    assert result.exit_code == 0


def test_sort_exits_zero_on_valid_file(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["sort", env_file])
    assert result.exit_code == 0


def test_sort_output_is_alphabetical(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["sort", env_file])
    output = result.output
    assert output.index("APPLE") < output.index("MANGO") < output.index("ZEBRA")


def test_sort_prefix_mode(runner, tmp_path):
    p = tmp_path / ".env"
    p.write_text("DB_PORT=5432\nAPP_NAME=myapp\nDB_HOST=localhost\n")
    cli = build_parser()
    result = runner.invoke(cli, ["sort", "--mode", "prefix", str(p)])
    assert result.exit_code == 0
    assert result.output.index("APP_NAME") < result.output.index("DB_HOST")


def test_sort_reports_summary(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["sort", env_file])
    lower = result.output.lower()
    assert "sort" in lower or "change" in lower or "key" in lower
