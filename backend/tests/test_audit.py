"""Audit recorder tests — every decision gets logged (PRD section 20)."""
import os
from app.audit.recorder import AuditRecorder


def test_record_entry():
    rec = AuditRecorder(path=None)
    entry = rec.record({"action": "DELETE_DATABASE", "decision": "BLOCKED"})
    assert entry["action"] == "DELETE_DATABASE"
    assert entry["decision"] == "BLOCKED"
    assert "timestamp" in entry


def test_all_returns_list():
    rec = AuditRecorder(path=None)
    rec.record({"action": "TEST", "decision": "AUTHORIZED"})
    rec.record({"action": "TEST2", "decision": "BLOCKED"})
    assert len(rec.all()) == 2


def test_all_returns_copy():
    rec = AuditRecorder(path=None)
    rec.record({"action": "X"})
    entries = rec.all()
    entries.clear()
    assert len(rec.all()) == 1


def test_jsonl_file_output(tmp_path):
    log_file = str(tmp_path / "audit.jsonl")
    rec = AuditRecorder(path=log_file)
    rec.record({"action": "TEST_FILE", "decision": "AUTHORIZED"})
    assert os.path.exists(log_file)
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) == 1
    assert "TEST_FILE" in lines[0]
