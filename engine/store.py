"""Tiny JSON file store with atomic writes (replaces a paid database)."""
from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path

_lock = threading.Lock()


def read_json(path: Path, default):
    path = Path(path)
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, default=str)
            os.replace(tmp, path)  # atomic on Windows and POSIX
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
