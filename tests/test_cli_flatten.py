"""CLI integration tests for the `flatten` subcommand."""

from __future__ import annotations

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
        "DB__HOST=localhost\n"
        "DB__PORT=5432\n"
        "APP_KEY=mysecretkey\n"
        "APP__DEBUG=true\n"
    )
    return str(p)


def test_flatten_subcommand_exists(runner):
    cli = build_parser()
    result = runner.invoke(cli, ["flatten", "--help"])
    assert result.exit_code == 0


def test_flatten_exits_zero_on_valid_file(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["flatten", env_file])
    assert result.exit_code == 0


def test_flatten_output_contains_top_level_groups(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["flatten", env_file])
    assert "DB" in result.output
    assert "APP" in result.output


def test_flatten_json_flag_produces_valid_json(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["flatten", "--json", env_file])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "DB" in data


def test_flatten_custom_separator(runner, tmp_path):
    p = tmp_path / ".env"
    p.write_text("APP.HOST=web\nAPP.PORT=80\n")
    cli = build_parser()
    result = runner.invoke(cli, ["flatten", "--separator", ".", str(p)])
    assert result.exit_code == 0
    assert "APP" in result.output


def test_flatten_missing_file_exits_nonzero(runner, tmp_path):
    cli = build_parser()
    result = runner.invoke(cli, ["flatten", str(tmp_path / "missing.env")])
    assert result.exit_code != 0
