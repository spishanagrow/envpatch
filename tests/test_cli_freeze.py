"""CLI integration tests for the `freeze` subcommand."""
import pytest
from click.testing import CliRunner

from envpatch.cli import build_parser


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("SECRET_KEY=abc123\nDEBUG=true\n")
    return str(p)


def test_freeze_subcommand_exists(runner):
    cli = build_parser()
    result = runner.invoke(cli, ["freeze", "--help"])
    assert result.exit_code == 0


def test_freeze_exits_zero_on_success(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["freeze", env_file])
    assert result.exit_code == 0


def test_freeze_reports_frozen_key(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["freeze", env_file])
    assert "frozen" in result.output.lower()


def test_freeze_with_keys_option_freezes_only_named_key(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["freeze", env_file, "--keys", "SECRET_KEY"])
    assert result.exit_code == 0
    assert "SECRET_KEY" in result.output
