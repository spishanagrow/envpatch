"""CLI integration tests for the encrypt and decrypt subcommands."""

import os
import tempfile

import pytest
from click.testing import CliRunner

from envpatch.cli import build_parser
from envpatch.encryptor import generate_key


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("APP_NAME=myapp\nAPI_SECRET=topsecret\nDEBUG=true\n")
    return str(p)


@pytest.fixture()
def key_file(tmp_path):
    k = generate_key()
    p = tmp_path / "envpatch.key"
    p.write_bytes(k)
    return str(p)


def test_encrypt_subcommand_exists(runner):
    cli = build_parser()
    result = runner.invoke(cli, ["encrypt", "--help"])
    assert result.exit_code == 0


def test_decrypt_subcommand_exists(runner):
    cli = build_parser()
    result = runner.invoke(cli, ["decrypt", "--help"])
    assert result.exit_code == 0


def test_encrypt_exits_zero_on_valid_file(runner, env_file, key_file):
    cli = build_parser()
    result = runner.invoke(cli, ["encrypt", env_file, "--key-file", key_file])
    assert result.exit_code == 0


def test_encrypt_output_contains_enc_prefix(runner, env_file, key_file):
    cli = build_parser()
    result = runner.invoke(cli, ["encrypt", env_file, "--key-file", key_file])
    assert "enc:" in result.output


def test_encrypt_generate_key_creates_file(runner, env_file, tmp_path):
    cli = build_parser()
    new_key = str(tmp_path / "new.key")
    result = runner.invoke(cli, ["encrypt", env_file, "--generate-key", "--key-file", new_key])
    assert result.exit_code == 0
    assert os.path.exists(new_key)


def test_decrypt_restores_plain_values(runner, env_file, key_file, tmp_path):
    cli = build_parser()
    enc_out = str(tmp_path / "enc.env")
    runner.invoke(cli, ["encrypt", env_file, "--key-file", key_file, "--output", enc_out])
    result = runner.invoke(cli, ["decrypt", enc_out, "--key-file", key_file])
    assert result.exit_code == 0
    assert "topsecret" in result.output
