"""Tests for envpatch.exporter."""

from __future__ import annotations

import json

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.exporter import to_dict, to_json, to_shell, to_dotenv


@pytest.fixture()
def sample_file() -> EnvFile:
    entries = [
        EnvEntry(key="APP_NAME", value="myapp", line_number=1),
        EnvEntry(key="DB_PASSWORD", value="s3cr3t", line_number=2),
        EnvEntry(key="DEBUG", value="true", line_number=3),
    ]
    return EnvFile(entries=entries, raw_lines=["APP_NAME=myapp", "DB_PASSWORD=s3cr3t", "DEBUG=true"])


def test_to_dict_returns_all_keys(sample_file: EnvFile) -> None:
    result = to_dict(sample_file)
    assert result == {"APP_NAME": "myapp", "DB_PASSWORD": "s3cr3t", "DEBUG": "true"}


def test_to_dict_redacts_secrets(sample_file: EnvFile) -> None:
    result = to_dict(sample_file, redact=True)
    assert result["APP_NAME"] == "myapp"
    assert result["DB_PASSWORD"] == "***"
    assert result["DEBUG"] == "true"


def test_to_dict_custom_mask(sample_file: EnvFile) -> None:
    result = to_dict(sample_file, redact=True, mask="<hidden>")
    assert result["DB_PASSWORD"] == "<hidden>"


def test_to_json_valid_json(sample_file: EnvFile) -> None:
    output = to_json(sample_file)
    parsed = json.loads(output)
    assert parsed["APP_NAME"] == "myapp"


def test_to_json_redacted(sample_file: EnvFile) -> None:
    output = to_json(sample_file, redact=True)
    parsed = json.loads(output)
    assert parsed["DB_PASSWORD"] == "***"


def test_to_shell_export_prefix(sample_file: EnvFile) -> None:
    output = to_shell(sample_file)
    lines = output.splitlines()
    assert all(line.startswith("export ") for line in lines)


def test_to_shell_no_export_prefix(sample_file: EnvFile) -> None:
    output = to_shell(sample_file, export=False)
    assert not any(line.startswith("export ") for line in output.splitlines())


def test_to_shell_quotes_values_with_spaces() -> None:
    entries = [EnvEntry(key="GREETING", value="hello world", line_number=1)]
    env_file = EnvFile(entries=entries, raw_lines=["GREETING=hello world"])
    output = to_shell(env_file, export=False)
    assert output == 'GREETING="hello world"'


def test_to_shell_redacts_secrets(sample_file: EnvFile) -> None:
    output = to_shell(sample_file, redact=True)
    assert "s3cr3t" not in output
    assert "***" in output


def test_to_dotenv_round_trip(sample_file: EnvFile) -> None:
    output = to_dotenv(sample_file)
    lines = output.splitlines()
    assert "APP_NAME=myapp" in lines
    assert "DB_PASSWORD=s3cr3t" in lines
    assert "DEBUG=true" in lines


def test_to_dotenv_redacted(sample_file: EnvFile) -> None:
    output = to_dotenv(sample_file, redact=True)
    assert "s3cr3t" not in output
    assert "DB_PASSWORD=***" in output
