"""Before/after comparison after a memory change."""
from __future__ import annotations

from . import savings_calculator


def _pct(before: float, after: float) -> float | None:
    if not before:
        return None
    return round((after - before) / before * 100, 1)


def compare(before: dict, after: dict, memory_before: int, memory_after: int,
            architecture: str = "x86_64", pricing: dict | None = None, min_invocations: int = 5) -> dict:
    """`before`/`after` are metric snapshots. Returns deltas and a verdict."""
    if after.get("invocations", 0) < min_invocations:
        return {
            "verdict": "awaiting_data",
            "message": f"Need at least {min_invocations} invocations after the change (have {after.get('invocations', 0)}). Invoke the function and verify again.",
        }

    # Cost per 1,000 invocations lets us compare windows of different length.
    cost_before = savings_calculator.monthly_cost(memory_before, before["avg_duration_ms"], 1000, architecture, pricing)
    cost_after = savings_calculator.monthly_cost(memory_after, after["avg_duration_ms"], 1000, architecture, pricing)
    duration_change = _pct(before["avg_duration_ms"], after["avg_duration_ms"])
    cost_change = _pct(cost_before, cost_after)

    if cost_change is not None and cost_change < 0 and (duration_change or 0) <= 25:
        verdict = "improved"
    elif cost_change is not None and cost_change < 0:
        verdict = "cheaper_but_slower"
    elif (duration_change or 0) < 0:
        verdict = "faster_but_costlier"
    else:
        verdict = "no_improvement"

    return {
        "verdict": verdict,
        "memory_mb": {"before": memory_before, "after": memory_after},
        "avg_duration_ms": {"before": before["avg_duration_ms"], "after": after["avg_duration_ms"], "change_pct": duration_change},
        "max_duration_ms": {"before": before.get("max_duration_ms"), "after": after.get("max_duration_ms")},
        "errors": {"before": before.get("errors", 0), "after": after.get("errors", 0)},
        "cost_per_1000_invocations": {"before": round(cost_before, 8), "after": round(cost_after, 8), "change_pct": cost_change},
        "message": "Compare cost and duration together: lower memory is only a win if duration stays acceptable.",
    }
