import pytest
from envpatch.parser import EnvEntry, EnvFile
from envpatch.merger import merge_env_files, has_changes, summary, as_string


def _entry(key, value, quoted=False, comment=None, line=1):
    return EnvEntry(key=key, value=value, quoted=quoted, comment=comment, line=line)


@pytest.fixture
def base_file():
    return EnvFile(
        entries=[
            _entry("APP_NAME", "myapp", line=1),
            _entry("DB_HOST", "localhost", line=2),
            _entry("SECRET_KEY", "old-secret", line=3),
        ],
        raw="APP_NAME=myapp\nDB_HOST=localhost\nSECRET_KEY=old-secret",
    )


@pytest.fixture
def patch_file():
    return EnvFile(
        entries=[
            _entry("APP_NAME", "myapp", line=1),
            _entry("DB_HOST", "remotehost", line=2),
            _entry("NEW_KEY", "new-value", line=3),
        ],
        raw="APP_NAME=myapp\nDB_HOST=remotehost\nNEW_KEY=new-value",
    )


def test_merge_applies_modification(base_file, patch_file):
    result = merge_env_files(base_file, patch_file)
    assert "DB_HOST" in result.modified
    values = {e.key: e.value for e in result.entries if e.key}
    assert values["DB_HOST"] == "remotehost"


def test_merge_adds_new_key(base_file, patch_file):
    result = merge_env_files(base_file, patch_file)
    assert "NEW_KEY" in result.added
    values = {e.key: e.value for e in result.entries if e.key}
    assert values["NEW_KEY"] == "new-value"


def test_merge_removes_key(base_file, patch_file):
    result = merge_env_files(base_file, patch_file)
    assert "SECRET_KEY" in result.removed
    keys = [e.key for e in result.entries if e.key]
    assert "SECRET_KEY" not in keys


def test_merge_keep_removed_flag(base_file, patch_file):
    result = merge_env_files(base_file, patch_file, keep_removed=True)
    keys = [e.key for e in result.entries if e.key]
    assert "SECRET_KEY" in keys
    assert "SECRET_KEY" in result.removed


def test_merge_skip_keys(base_file, patch_file):
    result = merge_env_files(base_file, patch_file, skip_keys=["DB_HOST"])
    assert "DB_HOST" in result.skipped
    assert "DB_HOST" not in result.modified
    values = {e.key: e.value for e in result.entries if e.key}
    assert values["DB_HOST"] == "localhost"


def test_has_changes_true(base_file, patch_file):
    result = merge_env_files(base_file, patch_file)
    assert has_changes(result) is True


def test_has_changes_false_identical():
    ef = EnvFile(
        entries=[_entry("A", "1")],
        raw="A=1",
    )
    result = merge_env_files(ef, ef)
    assert has_changes(result) is False


def test_summary_contains_counts(base_file, patch_file):
    result = merge_env_files(base_file, patch_file)
    s = summary(result)
    assert "added" in s
    assert "modified" in s
    assert "removed" in s


def test_as_string_produces_valid_dotenv(base_file, patch_file):
    result = merge_env_files(base_file, patch_file)
    text = as_string(result)
    assert "DB_HOST=remotehost" in text
    assert "NEW_KEY=new-value" in text
    assert "SECRET_KEY" not in text
