"""Turn raw CloudWatch snapshots into a health summary."""
from __future__ import annotations


def summarize(metrics: dict, min_invocations: int = 1) -> dict:
    inv = metrics.get("invocations", 0) or 0
    errors = metrics.get("errors", 0) or 0
    throttles = metrics.get("throttles", 0) or 0
    if inv < min_invocations:
        status = "no_data"
    elif throttles > 0 or (errors / inv) > 0.05:
        status = "degraded"
    else:
        status = "healthy"
    return {
        "status": status,
        "error_rate_pct": round(errors / inv * 100, 2) if inv else 0.0,
        "throttle_rate_pct": round(throttles / (inv + throttles) * 100, 2) if (inv + throttles) else 0.0,
        "invocations": inv,
        "avg_duration_ms": metrics.get("avg_duration_ms", 0.0),
        "max_duration_ms": metrics.get("max_duration_ms", 0.0),
    }


def memory_utilization_pct(max_memory_used_mb: int | None, configured_mb: int) -> float | None:
    if not max_memory_used_mb or not configured_mb:
        return None
    return round(max_memory_used_mb / configured_mb * 100, 1)
