"""Tests for envpatch.timeline."""

import json
import pytest
from envpatch.parser import EnvEntry, EnvFile
from envpatch.snapshotter import take_snapshot
from envpatch.timeline import Timeline


def _entry(key: str, value: str, line: int = 1) -> EnvEntry:
    return EnvEntry(key=key, value=value, line=line, raw=f"{key}={value}")


def _make_file(*pairs) -> EnvFile:
    entries = [_entry(k, v, i + 1) for i, (k, v) in enumerate(pairs)]
    return EnvFile(entries=entries, raw="")


@pytest.fixture
def timeline():
    tl = Timeline(name="myapp")
    f1 = _make_file(("HOST", "localhost"), ("PORT", "5432"))
    f2 = _make_file(("HOST", "db.prod"), ("PORT", "5432"), ("DEBUG", "false"))
    f3 = _make_file(("HOST", "db.prod"), ("PORT", "5433"), ("DEBUG", "false"))
    tl.record(take_snapshot(f1, label="v1"))
    tl.record(take_snapshot(f2, label="v2"))
    tl.record(take_snapshot(f3, label="v3"))
    return tl


def test_record_appends_snapshot(timeline):
    assert len(timeline.snapshots) == 3


def test_latest_returns_last_snapshot(timeline):
    assert timeline.latest.label == "v3"


def test_earliest_returns_first_snapshot(timeline):
    assert timeline.earliest.label == "v1"


def test_at_returns_correct_snapshot(timeline):
    assert timeline.at(1).label == "v2"


def test_diff_adjacent_detects_changes(timeline):
    diff = timeline.diff_adjacent(1)
    assert "DEBUG" in diff.added
    assert "HOST" in diff.modified


def test_diff_adjacent_invalid_index_raises(timeline):
    with pytest.raises(IndexError):
        timeline.diff_adjacent(0)


def test_diff_range_first_to_last(timeline):
    diff = timeline.diff_range(0, 2)
    assert diff.has_changes is True
    assert "DEBUG" in diff.added


def test_to_dict_contains_name(timeline):
    d = timeline.to_dict()
    assert d["name"] == "myapp"
    assert len(d["snapshots"]) == 3


def test_to_json_valid_json(timeline):
    raw = timeline.to_json()
    parsed = json.loads(raw)
    assert parsed["name"] == "myapp"


def test_from_dict_roundtrip(timeline):
    d = timeline.to_dict()
    restored = Timeline.from_dict(d)
    assert restored.name == timeline.name
    assert len(restored.snapshots) == len(timeline.snapshots)


def test_from_json_roundtrip(timeline):
    raw = timeline.to_json()
    restored = Timeline.from_json(raw)
    assert restored.latest.label == "v3"


def test_empty_timeline_latest_is_none():
    tl = Timeline(name="empty")
    assert tl.latest is None
    assert tl.earliest is None
