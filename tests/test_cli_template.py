"""CLI integration tests for the `envpatch template` subcommand."""
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
        "APP_ENV=production\n"
        "DB_PASSWORD=supersecret\n"
        "API_KEY=mykey\n"
        "APP_NAME=myapp\n"
    )
    return str(p)


def test_template_subcommand_exists(runner):
    cli = build_parser()
    result = runner.invoke(cli, ["template", "--help"])
    assert result.exit_code == 0
    assert "template" in result.output.lower() or "Usage" in result.output


def test_template_exits_zero_on_valid_file(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["template", env_file])
    assert result.exit_code == 0


def test_template_output_contains_placeholder(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["template", env_file])
    assert "<YOUR_" in result.output or "<SECRET>" in result.output


def test_template_preserves_non_secret_value(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["template", env_file])
    assert "APP_ENV=production" in result.output


def test_template_writes_output_file(runner, env_file, tmp_path):
    out = tmp_path / ".env.example"
    cli = build_parser()
    result = runner.invoke(cli, ["template", env_file, "--output", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    content = out.read_text()
    assert "DB_PASSWORD" in content
    assert "supersecret" not in content


def test_template_missing_file_exits_nonzero(runner, tmp_path):
    cli = build_parser()
    result = runner.invoke(cli, ["template", str(tmp_path / "missing.env")])
    assert result.exit_code != 0
