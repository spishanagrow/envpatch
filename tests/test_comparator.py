"""Tests for envpatch.comparator."""

import pytest
from envpatch.snapshotter import Snapshot, take_snapshot
from envpatch.parser import EnvEntry, EnvFile
from envpatch.comparator import (
    compare_snapshots,
    format_snapshot_diff,
    SnapshotDiff,
)


def _entry(key: str, value: str, line: int = 1) -> EnvEntry:
    return EnvEntry(key=key, value=value, line=line, raw=f"{key}={value}")


def _make_file(*pairs) -> EnvFile:
    entries = [_entry(k, v, i + 1) for i, (k, v) in enumerate(pairs)]
    return EnvFile(entries=entries, raw="")


@pytest.fixture
def snap_before():
    f = _make_file(("DB_HOST", "localhost"), ("API_KEY", "secret123"), ("PORT", "5432"))
    return take_snapshot(f, label="v1")


@pytest.fixture
def snap_after():
    f = _make_file(
        ("DB_HOST", "db.prod.example.com"),
        ("API_KEY", "secret123"),
        ("NEW_FLAG", "true"),
    )
    return take_snapshot(f, label="v2")


def test_compare_detects_added_key(snap_before, snap_after):
    diff = compare_snapshots(snap_before, snap_after)
    assert "NEW_FLAG" in diff.added


def test_compare_detects_removed_key(snap_before, snap_after):
    diff = compare_snapshots(snap_before, snap_after)
    assert "PORT" in diff.removed


def test_compare_detects_modified_key(snap_before, snap_after):
    diff = compare_snapshots(snap_before, snap_after)
    assert "DB_HOST" in diff.modified


def test_compare_detects_unchanged_key(snap_before, snap_after):
    diff = compare_snapshots(snap_before, snap_after)
    assert "API_KEY" in diff.unchanged


def test_has_changes_true(snap_before, snap_after):
    diff = compare_snapshots(snap_before, snap_after)
    assert diff.has_changes is True


def test_has_changes_false(snap_before):
    diff = compare_snapshots(snap_before, snap_before)
    assert diff.has_changes is False


def test_total_changes_count(snap_before, snap_after):
    diff = compare_snapshots(snap_before, snap_after)
    assert diff.total_changes == 3  # 1 added + 1 removed + 1 modified


def test_labels_default_to_snapshot_labels(snap_before, snap_after):
    diff = compare_snapshots(snap_before, snap_after)
    assert diff.before_label == "v1"
    assert diff.after_label == "v2"


def test_labels_can_be_overridden(snap_before, snap_after):
    diff = compare_snapshots(snap_before, snap_after, before_label="old", after_label="new")
    assert diff.before_label == "old"
    assert diff.after_label == "new"


def test_to_dict_contains_expected_keys(snap_before, snap_after):
    diff = compare_snapshots(snap_before, snap_after)
    d = diff.to_dict()
    assert set(d.keys()) == {"before", "after", "added", "removed", "modified", "unchanged", "total_changes"}


def test_format_snapshot_diff_returns_string(snap_before, snap_after):
    diff = compare_snapshots(snap_before, snap_after)
    output = format_snapshot_diff(diff)
    assert isinstance(output, str)
    assert "DB_HOST" in output
    assert "NEW_FLAG" in output
    assert "PORT" in output
