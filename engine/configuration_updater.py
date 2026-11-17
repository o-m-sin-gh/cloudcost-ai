"""Preview and apply memory changes. Dry-run is the default everywhere."""
from __future__ import annotations


def preview(fn: dict, target_mb: int) -> dict:
    """Describe the change without touching AWS (this IS the dry-run)."""
    return {
        "dry_run": True,
        "function_name": fn["name"],
        "change": {"MemorySize": {"from": fn["memory_mb"], "to": target_mb}},
        "aws_calls_that_would_run": [
            f"lambda:UpdateFunctionConfiguration(FunctionName={fn['name']}, MemorySize={target_mb})",
            "lambda:GetFunctionConfiguration (wait until LastUpdateStatus == Successful)",
        ],
        "note": "Nothing was changed. Approve this record, then apply it to make the change.",
    }


def apply_memory(provider, function_name: str, target_mb: int) -> dict:
    """Perform the real change via the provider. Raises on failure."""
    return provider.update_memory(function_name, target_mb)
