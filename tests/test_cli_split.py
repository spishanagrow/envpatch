"""CLI integration tests for the `split` subcommand."""
import json
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
    p.write_text(
        "DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=myapp\nSECRET_KEY=abc123\n"
    )
    return str(p)


def test_split_subcommand_exists(runner):
    cli = build_parser()
    result = runner.invoke(cli, ["split", "--help"])
    assert result.exit_code == 0


def test_split_exits_zero_on_valid_file(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["split", env_file, "--prefix", "DB_"])
    assert result.exit_code == 0


def test_split_output_contains_bucket_name(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["split", env_file, "--prefix", "DB_"])
    assert "DB" in result.output


def test_split_output_contains_matched_key(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["split", env_file, "--prefix", "DB_"])
    assert "DB_HOST" in result.output


def test_split_multiple_prefixes(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["split", env_file, "--prefix", "DB_", "--prefix", "APP_"])
    assert result.exit_code == 0
    assert "APP" in result.output
    assert "DB" in result.output


def test_split_strip_prefix_flag(runner, env_file):
    cli = build_parser()
    result = runner.invoke(cli, ["split", env_file, "--prefix", "DB_", "--strip-prefix"])
    assert result.exit_code == 0
    assert "HOST" in result.output
