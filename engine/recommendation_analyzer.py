"""Combine function config + metrics + a recommendation into one analysis.

Two recommendation sources exist and are never mixed up:
  * "aws-compute-optimizer": passed through untouched (finding + reason codes)
  * "cloudcost-heuristic":   our own fallback, always labelled as such
"""
from __future__ import annotations

import math

from . import optimization_rules, savings_calculator

SOURCE_AWS = "aws-compute-optimizer"
SOURCE_HEURISTIC = "cloudcost-heuristic"

# Heuristic knobs (only used when Compute Optimizer gives nothing)
HEADROOM = 1.30      # keep 30% above the observed max memory
ROUND_TO_MB = 64
MIN_HEURISTIC_INVOCATIONS = 20


def heuristic_recommendation(fn: dict, metrics: dict, max_memory_used_mb: int | None) -> dict:
    """Fallback recommender. Needs the 'Max Memory Used' value from REPORT logs."""
    base = {
        "function_name": fn["name"],
        "arn": fn.get("arn", ""),
        "source": SOURCE_HEURISTIC,
        "current_memory_mb": fn["memory_mb"],
        "number_of_invocations": metrics.get("invocations", 0),
        "aws_monthly_savings_usd": None,
        "performance_risk": None,
        "recommended_memory_mb": None,
        "reason_codes": [],
    }
    if metrics.get("invocations", 0) < MIN_HEURISTIC_INVOCATIONS:
        return {**base, "finding": "Unavailable", "reason_codes": ["InsufficientData"]}
    if not max_memory_used_mb:
        return {**base, "finding": "Unavailable", "reason_codes": ["NoMemoryUsageData"]}

    target = int(math.ceil(max_memory_used_mb * HEADROOM / ROUND_TO_MB) * ROUND_TO_MB)
    target = max(optimization_rules.LAMBDA_MIN_MB, target)
    if target < fn["memory_mb"] * 0.9:
        return {**base, "finding": "NotOptimized", "reason_codes": ["MemoryOverprovisioned"], "recommended_memory_mb": target}
    return {**base, "finding": "Optimized", "reason_codes": [], "recommended_memory_mb": fn["memory_mb"]}


def _unavailable_text(reasons: list[str]) -> str:
    if "InsufficientData" in reasons or "NoMemoryUsageData" in reasons:
        return "Awaiting sufficient usage history; no recommendation yet. No savings are shown."
    if "Inconclusive" in reasons:
        return "Compute Optimizer cannot analyse this function (configured memory above 1,792 MB). No savings are shown."
    return "No recommendation is available for this function. No savings are shown."


def analyze(fn: dict, metrics: dict, rec: dict | None, settings: dict, pricing: dict | None = None) -> dict:
    """Build the full analysis row for one function. `rec` may be None."""
    arch = fn.get("architecture", "x86_64")
    period_days = metrics.get("period_days", 14)
    inv_month = savings_calculator.monthly_invocations(metrics.get("invocations", 0), period_days)
    avg_ms = metrics.get("avg_duration_ms", 0.0)
    current_cost = savings_calculator.monthly_cost(fn["memory_mb"], avg_ms, inv_month, arch, pricing)

    out = {
        "function_name": fn["name"],
        "current_memory_mb": fn["memory_mb"],
        "recommended_memory_mb": None,
        "finding": "Unavailable",
        "status": "awaiting_data",
        "reason_codes": [],
        "source": None,
        "current_monthly_cost": round(current_cost, 8),
        "recommended_monthly_cost": None,
        "monthly_savings": None,
        "annual_savings": None,
        "savings_source": "none",
        "savings_per_million_invocations": None,
        "performance_risk": None,
        "eligible": False,
        "rule_notes": [],
        "explanation": "",
        "action": "",
    }

    if rec is None or rec.get("finding") == "Unavailable":
        reasons = (rec or {}).get("reason_codes", [])
        out.update(
            source=(rec or {}).get("source"),
            reason_codes=reasons,
            explanation=_unavailable_text(reasons),
            action="Invoke the function more (Compute Optimizer needs 50+ invocations in 14 days and memory <= 1792 MB) and check again later.",
        )
        return out

    out.update(
        finding=rec["finding"],
        source=rec.get("source"),
        reason_codes=rec.get("reason_codes", []),
        performance_risk=rec.get("performance_risk"),
    )

    if rec["finding"] == "Optimized" or not rec.get("recommended_memory_mb"):
        out.update(
            status="optimized",
            recommended_memory_mb=fn["memory_mb"],
            explanation="The current memory setting already looks well sized.",
            action="No change needed.",
        )
        return out

    target = int(rec["recommended_memory_mb"])
    out["recommended_memory_mb"] = target

    if rec.get("aws_monthly_savings_usd") is not None:
        monthly = float(rec["aws_monthly_savings_usd"])
        out["savings_source"] = "aws"
        out["recommended_monthly_cost"] = round(current_cost - monthly, 8)
        out["monthly_savings"] = round(monthly, 8)
        out["annual_savings"] = round(12 * monthly, 8)
    elif target < fn["memory_mb"]:
        est = savings_calculator.estimate_savings(fn["memory_mb"], target, avg_ms, inv_month, arch, pricing)
        out["savings_source"] = "estimated"
        out["recommended_monthly_cost"] = est["recommended_monthly_cost"]
        out["monthly_savings"] = est["monthly_savings"]
        out["annual_savings"] = est["annual_savings"]
    # A memory INCREASE is performance-driven: duration should drop, but we cannot
    # predict by how much, so no savings figure is invented. Verify after applying.

    if out["savings_source"] == "estimated":
        out["savings_per_million_invocations"] = savings_calculator.savings_per_million_invocations(
            fn["memory_mb"], target, avg_ms, arch, pricing
        )

    ok, notes = optimization_rules.validate_change(
        function_name=fn["name"],
        state=fn.get("state", "Active"),
        current_mb=fn["memory_mb"],
        target_mb=target,
        monthly_savings=out["monthly_savings"],
        managed_prefix=settings["managed_prefix"],
        min_monthly_savings=settings["min_monthly_savings_usd"],
        max_reduction_pct=settings["max_reduction_pct"],
    )
    out["eligible"] = ok
    out["rule_notes"] = notes

    if target < fn["memory_mb"]:
        out["status"] = "opportunity"
        out["explanation"] = (
            f"Memory looks over-provisioned: {fn['memory_mb']} MB configured, {target} MB recommended."
        )
        out["action"] = "Review the recommendation, run a dry-run, then compare duration after applying."
    else:
        out["status"] = "increase_suggested"
        out["explanation"] = (
            f"Function looks under-provisioned: raising memory {fn['memory_mb']} -> {target} MB gives more CPU and may cut duration."
        )
        out["action"] = "Consider increasing memory; verify the cost impact after applying."
    return out
