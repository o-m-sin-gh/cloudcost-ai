"""Back up a function's configuration before it is changed."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .store import read_json, write_json


def save_backup(backups_dir: Path, fn: dict, record_id: str, context: dict) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = Path(backups_dir) / f"{fn['name']}__{stamp}__{record_id}.json"
    write_json(path, {"function": fn, "record_id": record_id, **context})
    return str(path)


def load_backup(path: str | Path) -> dict:
    data = read_json(Path(path), None)
    if not data:
        raise FileNotFoundError(f"Backup not found or unreadable: {path}")
    return data
