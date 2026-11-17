"""Lambda cost model.

Prices are public list prices (us-east-1) BEFORE the free allowance
(1M requests + 400,000 GB-s per month). Override them in config.yaml
for other regions. Every number produced here is an ESTIMATE.
"""
from __future__ import annotations

DEFAULT_PRICING = {
    "gb_second": {"x86_64": 0.0000166667, "arm64": 0.0000133334},
    "per_request": 0.0000002,  # $0.20 per 1M requests
}


def monthly_invocations(invocations: float, period_days: float) -> float:
    """Scale invocations seen in `period_days` to a 30-day month."""
    if not period_days or period_days <= 0:
        return 0.0
    return float(invocations) / float(period_days) * 30.0


def monthly_cost(
    memory_mb: int,
    avg_duration_ms: float,
    invocations_per_month: float,
    architecture: str = "x86_64",
    pricing: dict | None = None,
) -> float:
    p = pricing or DEFAULT_PRICING
    rate = p["gb_second"].get(architecture, p["gb_second"]["x86_64"])
    gb_seconds = (memory_mb / 1024.0) * (avg_duration_ms / 1000.0) * invocations_per_month
    return gb_seconds * rate + invocations_per_month * p["per_request"]


def estimate_savings(
    current_mb: int,
    target_mb: int,
    avg_duration_ms: float,
    invocations_per_month: float,
    architecture: str = "x86_64",
    pricing: dict | None = None,
    target_duration_ms: float | None = None,
) -> dict:
    """Compare current vs target memory.

    If `target_duration_ms` is unknown we assume duration is unchanged. That is
    optimistic for CPU-bound code (less memory means less CPU), which is why the
    result is labelled an estimate and must be verified after applying.
    """
    new_duration = avg_duration_ms if target_duration_ms is None else target_duration_ms
    cur = monthly_cost(current_mb, avg_duration_ms, invocations_per_month, architecture, pricing)
    new = monthly_cost(target_mb, new_duration, invocations_per_month, architecture, pricing)
    monthly = cur - new
    return {
        "current_monthly_cost": round(cur, 8),
        "recommended_monthly_cost": round(new, 8),
        "monthly_savings": round(monthly, 8),
        "annual_savings": round(12 * monthly, 8),  # Annual = 12 x Monthly
        "assumed_duration_ms": round(new_duration, 3),
    }


def savings_per_million_invocations(
    current_mb: int,
    target_mb: int,
    avg_duration_ms: float,
    architecture: str = "x86_64",
    pricing: dict | None = None,
) -> float:
    """What the same change would save if the function ran 1M times a month.

    Student demo workloads cost fractions of a cent, so this "at scale" figure is
    the only way to see the effect. It is a projection, never actual savings.
    """
    r = estimate_savings(current_mb, target_mb, avg_duration_ms, 1_000_000, architecture, pricing)
    return round(r["monthly_savings"], 4)
