"""Tests for envpatch.auditor module."""

import json
import os
import tempfile

import pytest

from envpatch.auditor import (
    AuditAction,
    AuditEntry,
    AuditLog,
    make_entry,
)


def test_audit_entry_has_timestamp():
    entry = make_entry(AuditAction.DIFF, "base.env", "target.env")
    assert entry.timestamp
    assert "T" in entry.timestamp  # ISO format


def test_audit_entry_captures_user(monkeypatch):
    monkeypatch.setenv("USER", "testuser")
    entry = make_entry(AuditAction.MERGE, "base.env", "patch.env")
    assert entry.user == "testuser"


def test_audit_entry_to_dict_contains_action_string():
    entry = make_entry(AuditAction.VALIDATE, "base.env")
    d = entry.to_dict()
    assert d["action"] == "validate"
    assert d["source_file"] == "base.env"
    assert d["target_file"] is None


def test_audit_entry_to_json_is_valid():
    entry = make_entry(AuditAction.REDACT, "secrets.env", keys_redacted=3)
    raw = entry.to_json()
    parsed = json.loads(raw)
    assert parsed["action"] == "redact"
    assert parsed["details"]["keys_redacted"] == 3


def test_audit_log_record_and_filter():
    log = AuditLog()
    log.record(make_entry(AuditAction.DIFF, "a.env", "b.env"))
    log.record(make_entry(AuditAction.MERGE, "a.env", "patch.env"))
    log.record(make_entry(AuditAction.DIFF, "c.env", "d.env"))

    diffs = log.filter_by_action(AuditAction.DIFF)
    assert len(diffs) == 2
    merges = log.filter_by_action(AuditAction.MERGE)
    assert len(merges) == 1


def test_audit_log_to_json_is_valid_list():
    log = AuditLog()
    log.record(make_entry(AuditAction.DIFF, "a.env"))
    raw = log.to_json()
    parsed = json.loads(raw)
    assert isinstance(parsed, list)
    assert parsed[0]["action"] == "diff"


def test_audit_log_save_and_load_roundtrip():
    log = AuditLog()
    log.record(make_entry(AuditAction.VALIDATE, "prod.env", issues=2))
    log.record(make_entry(AuditAction.MERGE, "base.env", "patch.env", keys_added=1))

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tmp:
        tmp_path = tmp.name

    try:
        log.save(tmp_path)
        loaded = AuditLog.load(tmp_path)
        assert len(loaded.entries) == 2
        assert loaded.entries[0].action == AuditAction.VALIDATE
        assert loaded.entries[1].details["keys_added"] == 1
    finally:
        os.unlink(tmp_path)


def test_audit_log_empty_entries():
    log = AuditLog()
    assert log.entries == []
    assert json.loads(log.to_json()) == []
