"""CLI integration tests for the `envpatch rename` subcommand."""

import textwrap

import pytest
from click.testing import CliRunner

from envpatch.cli import build_parser


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(textwrap.dedent("""\
        DB_HOST=localhost
        DB_PORT=5432
        SECRET_KEY=supersecret
    """))
    return str(p)


def test_rename_subcommand_exists(runner):
    cli = build_parser()
    result = runner.invoke(cli, ["rename", "--help"])
    assert result.exit_code == 0
    assert "rename" in result.output.lower()


def test_rename_exits_zero_on_success(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["rename", env_file, "DB_HOST=DATABASE_HOST"])
    assert result.exit_code == 0


def test_rename_reports_renamed_key(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["rename", env_file, "DB_HOST=DATABASE_HOST"])
    assert "DB_HOST" in result.output
    assert "DATABASE_HOST" in result.output


def test_rename_reports_missing_key(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["rename", env_file, "NONEXISTENT=SOMETHING"])
    assert "NONEXISTENT" in result.output


def test_rename_inplace_modifies_file(runner, env_file, tmp_path):
    cli = build_parser()
    runner.invoke(cli, ["rename", "--inplace", env_file, "DB_PORT=DATABASE_PORT"])
    content = open(env_file).read()
    assert "DATABASE_PORT" in content
    assert "DB_PORT" not in content


def test_rename_dry_run_does_not_modify_file(runner, env_file):
    cli = build_parser()
    original = open(env_file).read()
    runner.invoke(cli, ["rename", "--dry-run", env_file, "DB_HOST=DATABASE_HOST"])
    assert open(env_file).read() == original
