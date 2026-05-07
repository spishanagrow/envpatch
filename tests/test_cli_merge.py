import pytest
from click.testing import CliRunner
from envpatch.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def base_env_file(tmp_path):
    f = tmp_path / ".env.base"
    f.write_text("APP_NAME=myapp\nDB_HOST=localhost\nOLD_KEY=bye\n")
    return str(f)


@pytest.fixture
def patch_env_file(tmp_path):
    f = tmp_path / ".env.patch"
    f.write_text("APP_NAME=myapp\nDB_HOST=remotehost\nNEW_KEY=hello\n")
    return str(f)


def test_merge_subcommand_exists(runner):
    result = runner.invoke(cli, ["merge", "--help"])
    assert result.exit_code == 0


def test_merge_exits_zero_on_success(runner, base_env_file, patch_env_file):
    result = runner.invoke(cli, ["merge", base_env_file, patch_env_file])
    assert result.exit_code == 0


def test_merge_output_contains_modified_key(runner, base_env_file, patch_env_file):
    result = runner.invoke(cli, ["merge", base_env_file, patch_env_file])
    assert "DB_HOST" in result.output


def test_merge_output_contains_added_key(runner, base_env_file, patch_env_file):
    result = runner.invoke(cli, ["merge", base_env_file, patch_env_file])
    assert "NEW_KEY" in result.output


def test_merge_summary_shown(runner, base_env_file, patch_env_file):
    result = runner.invoke(cli, ["merge", base_env_file, patch_env_file])
    assert any(word in result.output for word in ["added", "modified", "removed", "change"])
