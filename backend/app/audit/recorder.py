"""Audit trail (PRD section 20). Every decision gets recorded — authorized OR blocked."""
from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Optional

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class AuditRecorder:
    def __init__(self, path: Optional[str] = "audit_log.jsonl"):
        self.path = str(_BACKEND_DIR / path) if path and not Path(path).is_absolute() else path
        self._entries: list[dict] = []
        if self.path and Path(self.path).exists():
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        self._entries.append(json.loads(line))

    def record(self, entry: dict) -> dict:
        full = {"timestamp": datetime.now(timezone.utc).isoformat(), **entry}
        self._entries.append(full)
        if self.path:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(full, default=str) + "\n")
        return full

    def all(self) -> list[dict]:
        return list(self._entries)