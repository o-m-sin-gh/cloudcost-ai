"""Audit records and the approval state machine.

previewed -> approved -> applied -> rolled_back
previewed -> rejected          approved -> failed / rejected
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from .store import read_json, write_json

TRANSITIONS = {
    "previewed": {"approved", "rejected"},
    "approved": {"applied", "failed", "rejected"},
    "applied": {"rolled_back"},
    "failed": set(),
    "rejected": set(),
    "rolled_back": set(),
}


class ApprovalError(Exception):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ApprovalManager:
    def __init__(self, history_dir: Path):
        self.path = Path(history_dir) / "optimizations.json"

    def _all(self) -> list[dict]:
        return read_json(self.path, [])

    def list(self) -> list[dict]:
        return sorted(self._all(), key=lambda r: r["created_at"], reverse=True)

    def get(self, record_id: str) -> dict:
        for r in self._all():
            if r["id"] == record_id:
                return r
        raise ApprovalError(f"Unknown record '{record_id}'.")

    def create(self, **fields) -> dict:
        record = {
            "id": uuid.uuid4().hex[:12],
            "created_at": now_iso(),
            "status": "previewed",
            "approved_at": None,
            "applied_at": None,
            "new_memory_mb": None,
            "backup_file": None,
            "api_result": None,
            "verification": None,
            "rollback": None,
            "error": None,
            **fields,
        }
        records = self._all()
        records.append(record)
        write_json(self.path, records)
        return record

    def transition(self, record_id: str, new_status: str, **fields) -> dict:
        records = self._all()
        for r in records:
            if r["id"] == record_id:
                if new_status not in TRANSITIONS.get(r["status"], set()):
                    raise ApprovalError(f"Cannot move a '{r['status']}' record to '{new_status}'.")
                r["status"] = new_status
                r.update(fields)
                write_json(self.path, records)
                return r
        raise ApprovalError(f"Unknown record '{record_id}'.")

    def update(self, record_id: str, **fields) -> dict:
        """Update non-status fields (e.g. verification results)."""
        records = self._all()
        for r in records:
            if r["id"] == record_id:
                r.update(fields)
                write_json(self.path, records)
                return r
        raise ApprovalError(f"Unknown record '{record_id}'.")
