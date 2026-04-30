"""Tests for envpatch.tagger."""
import pytest
from envpatch.parser import EnvEntry, EnvFile
from envpatch.tagger import TagResult, tag_file, filter_by_tag, _parse_tags_from_comment


def _entry(key: str, value: str = "val", comment: str = None) -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=comment, line_number=1, raw=f"{key}={value}")


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries), raw_lines=[])


def test_tag_file_applies_explicit_map():
    f = _make_file(_entry("DB_HOST"), _entry("API_KEY"))
    result = tag_file(f, {"DB_HOST": {"database"}, "API_KEY": {"auth", "secret"}})
    assert "database" in result.tags_for("DB_HOST")
    assert "auth" in result.tags_for("API_KEY")
    assert "secret" in result.tags_for("API_KEY")


def test_tag_file_parses_embedded_comment_tags():
    e = _entry("REDIS_URL", comment="@tags: cache, infra")
    f = _make_file(e)
    result = tag_file(f, {})
    assert "cache" in result.tags_for("REDIS_URL")
    assert "infra" in result.tags_for("REDIS_URL")


def test_tag_file_merges_explicit_and_embedded():
    e = _entry("REDIS_URL", comment="@tags: cache")
    f = _make_file(e)
    result = tag_file(f, {"REDIS_URL": {"infra"}})
    assert "cache" in result.tags_for("REDIS_URL")
    assert "infra" in result.tags_for("REDIS_URL")


def test_keys_with_tag_returns_correct_keys():
    f = _make_file(_entry("DB_HOST"), _entry("DB_PASS"), _entry("API_KEY"))
    result = tag_file(f, {"DB_HOST": {"database"}, "DB_PASS": {"database", "secret"}, "API_KEY": {"auth"}})
    db_keys = result.keys_with_tag("database")
    assert "DB_HOST" in db_keys
    assert "DB_PASS" in db_keys
    assert "API_KEY" not in db_keys


def test_all_tags_aggregates_unique_tags():
    f = _make_file(_entry("A"), _entry("B"), _entry("C"))
    result = tag_file(f, {"A": {"x", "y"}, "B": {"y", "z"}, "C": {"z"}})
    assert result.all_tags() == {"x", "y", "z"}


def test_filter_by_tag_returns_matching_entries():
    f = _make_file(_entry("DB_HOST"), _entry("API_KEY"), _entry("LOG_LEVEL"))
    result = tag_file(f, {"DB_HOST": {"database"}, "LOG_LEVEL": {"logging"}})
    filtered = filter_by_tag(result, "database")
    assert len(filtered) == 1
    assert filtered[0].key == "DB_HOST"


def test_parse_tags_ignores_non_tag_comments():
    tags = _parse_tags_from_comment("some random comment")
    assert tags == set()


def test_summary_reports_counts():
    f = _make_file(_entry("A"), _entry("B"))
    result = tag_file(f, {"A": {"x"}, "B": {"x", "y"}})
    s = result.summary()
    assert "2 tagged" in s
    assert "2 unique" in s
