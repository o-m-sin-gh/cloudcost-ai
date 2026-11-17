"""Restore the memory setting saved in the backup."""
from __future__ import annotations

from .configuration_backup import load_backup


def rollback(provider, record: dict) -> dict:
    if not record.get("backup_file"):
        raise ValueError("This record has no backup file; cannot roll back.")
    backup = load_backup(record["backup_file"])
    original_mb = backup["function"]["memory_mb"]
    result = provider.update_memory(record["function_name"], original_mb)
    return {"restored_memory_mb": original_mb, "api_result": result}
