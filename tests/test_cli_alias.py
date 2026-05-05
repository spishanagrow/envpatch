"""CLI integration tests for the `alias` subcommand."""
import json
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
        "DATABASE_PASSWORD=s3cr3t\n"
        "DATABASE_HOST=localhost\n"
        "APP_PORT=8080\n"
    )
    return str(p)


def test_alias_subcommand_exists(runner):
    result = runner.invoke(build_parser(), ["alias", "--help"])
    assert result.exit_code == 0


def test_alias_exits_zero_on_success(runner, env_file):
    result = runner.invoke(
        build_parser(),
        ["alias", env_file, "--map", "db_pass=DATABASE_PASSWORD"],
    )
    assert result.exit_code == 0


def test_alias_output_contains_alias_name(runner, env_file):
    result = runner.invoke(
        build_parser(),
        ["alias", env_file, "--map", "db_pass=DATABASE_PASSWORD"],
    )
    assert "db_pass" in result.output


def test_alias_reports_unresolved(runner, env_file):
    result = runner.invoke(
        build_parser(),
        ["alias", env_file, "--map", "ghost=NONEXISTENT_KEY"],
    )
    assert result.exit_code == 0
    assert "ghost" in result.output


def test_alias_multiple_maps(runner, env_file):
    result = runner.invoke(
        build_parser(),
        [
            "alias", env_file,
            "--map", "host=DATABASE_HOST",
            "--map", "port=APP_PORT",
        ],
    )
    assert result.exit_code == 0
    assert "host" in result.output
    assert "port" in result.output
