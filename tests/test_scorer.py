"""Tests for envpatch.scorer."""
import pytest
from envpatch.parser import EnvFile, EnvEntry
from envpatch.scorer import score_file, _grade, ScoreReport


def _entry(key: str, value: str, line: int = 1) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", line=line)


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries), source="test")


# ---------------------------------------------------------------------------
# grade helper
# ---------------------------------------------------------------------------

def test_grade_a():
    assert _grade(95) == "A"
    assert _grade(90) == "A"


def test_grade_b():
    assert _grade(80) == "B"
    assert _grade(75) == "B"


def test_grade_f():
    assert _grade(30) == "F"


# ---------------------------------------------------------------------------
# score_file
# ---------------------------------------------------------------------------

def test_empty_file_scores_100():
    env = _make_file()
    report = score_file(env)
    assert report.score == 100
    assert report.grade == "A"
    assert report.total_keys == 0


def test_clean_file_scores_high():
    env = _make_file(
        _entry("HOST", "localhost", 1),
        _entry("PORT", "5432", 2),
        _entry("DEBUG", "false", 3),
    )
    report = score_file(env)
    assert report.score >= 90
    assert report.grade == "A"
    assert report.penalties == []


def test_placeholder_values_reduce_score():
    env = _make_file(
        _entry("API_KEY", "<YOUR_API_KEY>", 1),
        _entry("DB_PASS", "changeme", 2),
        _entry("HOST", "localhost", 3),
    )
    report = score_file(env)
    assert report.placeholder_keys == 2
    assert report.score < 100
    assert any("placeholder" in p for p in report.penalties)


def test_empty_values_reduce_score():
    env = _make_file(
        _entry("SECRET", "", 1),
        _entry("HOST", "localhost", 2),
        _entry("PORT", "5432", 3),
    )
    report = score_file(env)
    assert report.empty_keys == 1
    assert report.score < 100
    assert any("empty" in p for p in report.penalties)


def test_few_keys_penalty():
    env = _make_file(
        _entry("HOST", "localhost", 1),
    )
    report = score_file(env)
    assert any("fewer than 3" in p for p in report.penalties)


def test_to_dict_contains_expected_keys():
    env = _make_file(
        _entry("HOST", "localhost", 1),
        _entry("PORT", "5432", 2),
        _entry("DEBUG", "true", 3),
    )
    d = score_file(env).to_dict()
    for key in ("total_keys", "secret_keys", "placeholder_keys", "empty_keys", "score", "grade", "penalties"):
        assert key in d


def test_score_clamped_at_zero():
    """Even with many issues, score never goes below 0."""
    entries = [_entry(f"K{i}", "changeme", i) for i in range(20)]
    env = _make_file(*entries)
    report = score_file(env)
    assert report.score >= 0
