"""CLI integration tests for the `pin` subcommand."""

import os
import tempfile

import pytest
from click.testing import CliRunner

from envpatch.cli import build_parser


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("API_KEY=secret\nDEBUG=true\n")
    return str(p)


def test_pin_subcommand_exists(runner):
    cli = build_parser()
    result = runner.invoke(cli, ["pin", "--help"])
    assert result.exit_code == 0


def test_pin_exits_zero_on_success(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["pin", env_file, "API_KEY"])
    assert result.exit_code == 0


def test_pin_reports_pinned_key(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["pin", env_file, "API_KEY"])
    assert "API_KEY" in result.output or "Pinned" in result.output


def test_pin_reports_skipped_unknown_key(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["pin", env_file, "DOES_NOT_EXIST"])
    assert result.exit_code == 0
    assert "DOES_NOT_EXIST" in result.output or "skipped" in result.output.lower()


def test_pin_writes_marker_to_file(runner, env_file):
    cli = build_parser()
    runner.invoke(cli, ["pin", env_file, "DEBUG"])
    content = open(env_file).read()
    assert "# pinned" in content
