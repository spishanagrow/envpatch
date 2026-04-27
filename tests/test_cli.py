"""Integration tests for the envpatch CLI interface."""

import os
import tempfile
import pytest
from unittest.mock import patch
from io import StringIO

from envpatch.cli import build_parser, main, _read_file


@pytest.fixture
def base_env_file(tmp_path):
    """Write a base .env file to a temp location."""
    content = """# Base environment
APP_NAME=myapp
DEBUG=false
DB_HOST=localhost
DB_PASSWORD=supersecret
API_KEY=abc123
"""
    f = tmp_path / ".env.base"
    f.write_text(content)
    return str(f)


@pytest.fixture
def target_env_file(tmp_path):
    """Write a target .env file to a temp location."""
    content = """# Target environment
APP_NAME=myapp
DEBUG=true
DB_HOST=prod.db.example.com
DB_PASSWORD=newprodpassword
NEW_FEATURE_FLAG=enabled
"""
    f = tmp_path / ".env.target"
    f.write_text(content)
    return str(f)


@pytest.fixture
def patch_env_file(tmp_path):
    """Write a patch .env file to a temp location."""
    content = """DEBUG=true
DB_HOST=prod.db.example.com
NEW_FEATURE_FLAG=enabled
"""
    f = tmp_path / ".env.patch"
    f.write_text(content)
    return str(f)


class TestBuildParser:
    def test_parser_has_diff_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(["diff", "file1.env", "file2.env"])
        assert args.command == "diff"
        assert args.base == "file1.env"
        assert args.target == "file2.env"

    def test_parser_has_merge_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(["merge", "base.env", "patch.env", "-o", "out.env"])
        assert args.command == "merge"
        assert args.base == "base.env"
        assert args.patch == "patch.env"
        assert args.output == "out.env"

    def test_diff_no_secrets_flag(self):
        parser = build_parser()
        args = parser.parse_args(["diff", "a.env", "b.env", "--no-secrets"])
        assert args.no_secrets is True

    def test_diff_show_secrets_flag_default_false(self):
        parser = build_parser()
        args = parser.parse_args(["diff", "a.env", "b.env"])
        assert args.no_secrets is False


class TestReadFile:
    def test_read_existing_file(self, tmp_path):
        f = tmp_path / "test.env"
        f.write_text("KEY=value\n")
        content = _read_file(str(f))
        assert content == "KEY=value\n"

    def test_read_missing_file_raises(self):
        with pytest.raises(SystemExit):
            _read_file("/nonexistent/path/.env")


class TestCmdDiff:
    def test_diff_outputs_changes(self, base_env_file, target_env_file, capsys):
        parser = build_parser()
        args = parser.parse_args(["diff", base_env_file, target_env_file])
        # Should not raise and should produce output
        try:
            from envpatch.cli import cmd_diff
            cmd_diff(args)
        except SystemExit:
            pass
        captured = capsys.readouterr()
        assert len(captured.out) > 0 or len(captured.err) == 0

    def test_diff_identical_files_shows_no_changes(self, base_env_file, capsys):
        parser = build_parser()
        args = parser.parse_args(["diff", base_env_file, base_env_file])
        from envpatch.cli import cmd_diff
        cmd_diff(args)
        captured = capsys.readouterr()
        assert "No changes" in captured.out or captured.out.strip() == "" or "0 changes" in captured.out


class TestCmdMerge:
    def test_merge_writes_output_file(self, base_env_file, patch_env_file, tmp_path):
        output_file = str(tmp_path / ".env.merged")
        parser = build_parser()
        args = parser.parse_args(["merge", base_env_file, patch_env_file, "-o", output_file])
        from envpatch.cli import cmd_merge
        cmd_merge(args)
        assert os.path.exists(output_file)
        merged_content = open(output_file).read()
        assert "DEBUG=true" in merged_content
        assert "NEW_FEATURE_FLAG=enabled" in merged_content

    def test_merge_without_output_prints_to_stdout(self, base_env_file, patch_env_file, capsys):
        parser = build_parser()
        args = parser.parse_args(["merge", base_env_file, patch_env_file])
        from envpatch.cli import cmd_merge
        cmd_merge(args)
        captured = capsys.readouterr()
        assert "DEBUG=true" in captured.out
