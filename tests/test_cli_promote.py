"""CLI integration tests for the 'promote' subcommand."""
import pytest
from click.testing import CliRunner

from envpatch.cli import build_parser


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def source_env(tmp_path):
    p = tmp_path / "prod.env"
    p.write_text("DB_HOST=prod-db.example.com\nAPI_KEY=secret\nDEBUG=false\n")
    return str(p)


@pytest.fixture
def target_env(tmp_path):
    p = tmp_path / "staging.env"
    p.write_text("DB_HOST=localhost\nDEBUG=true\n")
    return str(p)


def test_promote_subcommand_exists(runner):
    cli = build_parser()
    result = runner.invoke(cli, ["promote", "--help"])
    assert result.exit_code == 0


def test_promote_exits_zero_on_success(runner, source_env, target_env):
    cli = build_parser()
    result = runner.invoke(cli, ["promote", source_env, target_env])
    assert result.exit_code == 0


def test_promote_output_contains_summary(runner, source_env, target_env):
    cli = build_parser()
    result = runner.invoke(cli, ["promote", source_env, target_env])
    assert "Promoted" in result.output


def test_promote_with_key_filter(runner, source_env, target_env):
    cli = build_parser()
    result = runner.invoke(
        cli, ["promote", source_env, target_env, "--key", "DB_HOST"]
    )
    assert result.exit_code == 0
    assert "DB_HOST" in result.output


def test_promote_no_overwrite_flag(runner, source_env, target_env):
    cli = build_parser()
    result = runner.invoke(
        cli, ["promote", source_env, target_env, "--no-overwrite"]
    )
    assert result.exit_code == 0
