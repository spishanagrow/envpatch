"""CLI integration tests for the 'group' subcommand."""
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
        "APP_ENV=production\n"
        "SECRET_KEY=abc123\n"
    )
    return str(p)


def test_group_subcommand_exists(runner):
    cli = build_parser()
    result = runner.invoke(cli, ["group", "--help"])
    assert result.exit_code == 0


def test_group_exits_zero_on_valid_file(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["group", env_file])
    assert result.exit_code == 0


def test_group_output_contains_prefix(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["group", env_file])
    assert "DB" in result.output
    assert "APP" in result.output


def test_group_ungrouped_section_present(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["group", env_file])
    assert "ungrouped" in result.output
    assert "SECRET_KEY" in result.output


def test_group_min_size_flag(runner, env_file):
    cli = build_parser()
    # With min-group-size=3, DB (2 keys) should be demoted
    result = runner.invoke(cli, ["group", "--min-group-size", "3", env_file])
    assert result.exit_code == 0
    # APP (2 keys) and DB (2 keys) both < 3, all ungrouped
    assert "[DB]" not in result.output
