"""Tests for envpatch.snapshotter."""
import json
import pytest

from envpatch.parser import EnvFile, EnvEntry
from envpatch.snapshotter import (
    Snapshot,
    take_snapshot,
    snapshots_differ,
    changed_keys,
    _checksum,
)


def _entry(key: str, value: str, line: int = 1) -> EnvEntry:
    return EnvEntry(key=key, value=value, line_number=line, raw=f"{key}={value}")


@pytest.fixture
def simple_file() -> EnvFile:
    return EnvFile(
        entries=[
            _entry("APP_NAME", "myapp", 1),
            _entry("SECRET_KEY", "s3cr3t", 2),
            _entry("DEBUG", "false", 3),
        ]
    )


def test_take_snapshot_returns_snapshot(simple_file):
    snap = take_snapshot(simple_file, label="v1")
    assert isinstance(snap, Snapshot)
    assert snap.label == "v1"


def test_snapshot_has_timestamp(simple_file):
    snap = take_snapshot(simple_file, label="v1")
    assert snap.timestamp  # non-empty ISO string
    assert "T" in snap.timestamp  # basic ISO-8601 check


def test_snapshot_checksum_is_hex(simple_file):
    snap = take_snapshot(simple_file, label="v1")
    assert len(snap.checksum) == 64
    int(snap.checksum, 16)  # must be valid hex


def test_snapshot_redacts_secrets(simple_file):
    snap = take_snapshot(simple_file, label="v1", mask="REDACTED")
    assert snap.entries["SECRET_KEY"] == "REDACTED"
    assert snap.entries["APP_NAME"] == "myapp"  # plain key kept


def test_snapshot_to_dict_roundtrip(simple_file):
    snap = take_snapshot(simple_file, label="v1")
    d = snap.to_dict()
    restored = Snapshot.from_dict(d)
    assert restored.label == snap.label
    assert restored.checksum == snap.checksum
    assert restored.entries == snap.entries


def test_snapshot_to_json_is_valid(simple_file):
    snap = take_snapshot(simple_file, label="v1")
    raw = snap.to_json()
    parsed = json.loads(raw)
    assert parsed["label"] == "v1"
    assert "entries" in parsed


def test_snapshots_differ_same_file(simple_file):
    a = take_snapshot(simple_file, label="a")
    b = take_snapshot(simple_file, label="b")
    assert not snapshots_differ(a, b)


def test_snapshots_differ_changed_value():
    f1 = EnvFile(entries=[_entry("KEY", "old")])
    f2 = EnvFile(entries=[_entry("KEY", "new")])
    a = take_snapshot(f1, label="a")
    b = take_snapshot(f2, label="b")
    assert snapshots_differ(a, b)


def test_changed_keys_detects_modification():
    f1 = EnvFile(entries=[_entry("KEY", "old"), _entry("STABLE", "same")])
    f2 = EnvFile(entries=[_entry("KEY", "new"), _entry("STABLE", "same")])
    a = take_snapshot(f1, label="a")
    b = take_snapshot(f2, label="b")
    diff = changed_keys(a, b)
    assert "KEY" in diff
    assert "STABLE" not in diff


def test_changed_keys_detects_added_and_removed():
    f1 = EnvFile(entries=[_entry("OLD_KEY", "x")])
    f2 = EnvFile(entries=[_entry("NEW_KEY", "y")])
    a = take_snapshot(f1, label="a")
    b = take_snapshot(f2, label="b")
    diff = changed_keys(a, b)
    assert "OLD_KEY" in diff
    assert "NEW_KEY" in diff
    assert diff["OLD_KEY"] == ("x", None)
    assert diff["NEW_KEY"] == (None, "y")
