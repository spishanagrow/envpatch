"""CLI integration tests for the `clone` subcommand."""
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
        "APP_NAME=myapp\n"
        "DB_HOST=localhost\n"
        "DB_PASSWORD=s3cr3t\n"
        "API_KEY=abc123\n"
    )
    return str(p)


def test_clone_subcommand_exists(runner):
    cli = build_parser()
    result = runner.invoke(cli, ["clone", "--help"])
    assert result.exit_code == 0


def test_clone_exits_zero_on_success(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["clone", env_file])
    assert result.exit_code == 0


def test_clone_output_contains_all_keys_by_default(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["clone", env_file])
    assert "APP_NAME" in result.output
    assert "DB_HOST" in result.output


def test_clone_prefix_filter_limits_output(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["clone", env_file, "--prefix", "DB_"])
    assert "DB_HOST" in result.output
    assert "APP_NAME" not in result.output


def test_clone_exclude_secrets_omits_secret_keys(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["clone", env_file, "--exclude-secrets"])
    assert "API_KEY" not in result.output
    assert "APP_NAME" in result.output
