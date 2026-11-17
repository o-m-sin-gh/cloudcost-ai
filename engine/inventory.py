"""Normalise Lambda function configuration into the shape the app uses."""
from __future__ import annotations


def normalize_function(cfg: dict) -> dict:
    return {
        "name": cfg["FunctionName"],
        "arn": cfg.get("FunctionArn", ""),
        "runtime": cfg.get("Runtime", cfg.get("PackageType", "n/a")),
        "memory_mb": int(cfg.get("MemorySize", 128)),
        "timeout_s": int(cfg.get("Timeout", 3)),
        "architecture": (cfg.get("Architectures") or ["x86_64"])[0],
        "last_modified": cfg.get("LastModified", ""),
        "state": cfg.get("State", "Active"),
        "last_update_status": cfg.get("LastUpdateStatus", "Successful"),
    }


def sort_inventory(functions: list[dict]) -> list[dict]:
    return sorted(functions, key=lambda f: f["name"].lower())
