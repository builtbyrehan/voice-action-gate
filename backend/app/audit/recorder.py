"""Audit trail (PRD section 20). Every decision gets recorded — authorized OR blocked."""
from datetime import datetime, timezone
import json
from typing import Optional


class AuditRecorder:
    def __init__(self, path: Optional[str] = "audit_log.jsonl"):
        self.path = path
        self._entries: list[dict] = []

    def record(self, entry: dict) -> dict:
        full = {"timestamp": datetime.now(timezone.utc).isoformat(), **entry}
        self._entries.append(full)
        if self.path:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(full, default=str) + "\n")
        return full

    def all(self) -> list[dict]:
        return list(self._entries)