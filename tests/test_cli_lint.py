"""Integration tests for the `envpatch lint` CLI sub-command."""
import textwrap
import pytest
from click.testing import CliRunner

from envpatch.cli import build_parser


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def clean_env(tmp_path):
    p = tmp_path / ".env"
    p.write_text(textwrap.dedent("""\
        DATABASE_URL=postgres://localhost/db
        SECRET_KEY=s3cr3t
        DEBUG=false
    """))
    return str(p)


@pytest.fixture()
def dirty_env(tmp_path):
    p = tmp_path / ".env"
    p.write_text(textwrap.dedent("""\
        database_url=postgres://localhost/db
        SECRET_KEY=s3cr3t
        SECRET_KEY=duplicate
        debug=false
    """))
    return str(p)


def test_lint_subcommand_exists(runner):
    cli = build_parser()
    result = runner.invoke(cli, ["lint", "--help"])
    assert result.exit_code == 0


def test_lint_clean_file_exits_zero(runner, clean_env):
    cli = build_parser()
    result = runner.invoke(cli, ["lint", clean_env])
    assert result.exit_code == 0


def test_lint_clean_file_prints_ok(runner, clean_env):
    cli = build_parser()
    result = runner.invoke(cli, ["lint", clean_env])
    assert "No lint issues" in result.output or "OK" in result.output


def test_lint_dirty_file_exits_nonzero(runner, dirty_env):
    cli = build_parser()
    result = runner.invoke(cli, ["lint", dirty_env])
    assert result.exit_code != 0


def test_lint_dirty_file_reports_issues(runner, dirty_env):
    cli = build_parser()
    result = runner.invoke(cli, ["lint", dirty_env])
    output = result.output
    assert "KEY_NOT_UPPERCASE" in output or "DUPLICATE_KEY" in output


def test_lint_missing_file_exits_with_error(runner, tmp_path):
    cli = build_parser()
    result = runner.invoke(cli, ["lint", str(tmp_path / "nonexistent.env")])
    assert result.exit_code != 0
