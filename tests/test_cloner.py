"""Tests for envpatch.cloner."""
from envpatch.parser import EnvEntry, EnvFile
from envpatch.cloner import CloneResult, clone_file


def _entry(key: str, value: str = "val", line: int = 1) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", line=line)


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# clone_file – no filters
# ---------------------------------------------------------------------------

def test_clone_all_keys_by_default():
    f = _make_file(_entry("A"), _entry("B"), _entry("C"))
    result = clone_file(f, source_key="test")
    assert result.cloned_count == 3
    assert result.skipped_count == 0


def test_clone_result_as_envfile_contains_cloned_entries():
    f = _make_file(_entry("X"), _entry("Y"))
    result = clone_file(f)
    cloned_file = result.as_envfile()
    keys = [e.key for e in cloned_file.entries]
    assert "X" in keys and "Y" in keys


# ---------------------------------------------------------------------------
# clone_file – keys filter
# ---------------------------------------------------------------------------

def test_clone_with_keys_filter_includes_only_listed_keys():
    f = _make_file(_entry("A"), _entry("B"), _entry("C"))
    result = clone_file(f, keys=["A", "C"])
    cloned_keys = [e.key for e in result.cloned if e.key]
    assert cloned_keys == ["A", "C"]
    assert result.skipped_count == 1


def test_clone_with_keys_filter_missing_key_is_skipped():
    f = _make_file(_entry("A"), _entry("B"))
    result = clone_file(f, keys=["Z"])
    assert result.cloned_count == 0
    assert result.skipped_count == 2


# ---------------------------------------------------------------------------
# clone_file – prefix filter
# ---------------------------------------------------------------------------

def test_clone_with_prefix_keeps_matching_keys():
    f = _make_file(_entry("DB_HOST"), _entry("DB_PORT"), _entry("APP_NAME"))
    result = clone_file(f, prefix="DB_")
    cloned_keys = [e.key for e in result.cloned if e.key]
    assert cloned_keys == ["DB_HOST", "DB_PORT"]


def test_clone_with_prefix_skips_non_matching():
    f = _make_file(_entry("DB_HOST"), _entry("APP_NAME"))
    result = clone_file(f, prefix="DB_")
    assert result.skipped_count == 1


# ---------------------------------------------------------------------------
# clone_file – exclude_secrets
# ---------------------------------------------------------------------------

def test_clone_exclude_secrets_skips_secret_keys():
    f = _make_file(_entry("API_KEY", "abc123"), _entry("APP_NAME", "myapp"))
    result = clone_file(f, exclude_secrets=True)
    cloned_keys = [e.key for e in result.cloned if e.key]
    assert "API_KEY" not in cloned_keys
    assert "APP_NAME" in cloned_keys


def test_clone_exclude_secrets_false_keeps_secret_keys():
    f = _make_file(_entry("API_SECRET", "s3cr3t"), _entry("HOST", "localhost"))
    result = clone_file(f, exclude_secrets=False)
    cloned_keys = [e.key for e in result.cloned if e.key]
    assert "API_SECRET" in cloned_keys


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------

def test_summary_contains_source_key_and_counts():
    f = _make_file(_entry("A"), _entry("B"), _entry("C"))
    result = clone_file(f, source_key=".env.prod", keys=["A"])
    s = result.summary()
    assert ".env.prod" in s
    assert "1" in s  # cloned
