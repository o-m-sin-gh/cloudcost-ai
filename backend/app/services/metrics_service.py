from __future__ import annotations

from datetime import datetime, timedelta, timezone

from engine import metrics_analyzer
from engine.store import read_json, write_json

from .state import Ctx, utcnow


def get_function_metrics(ctx: Ctx, name: str, days: int | None = None, force: bool = False) -> dict:
    """CloudWatch snapshot for the last `days`, cached to local JSON to save API calls."""
    days = days or ctx.settings.lookback_days
    path = ctx.settings.data_dir / "metrics" / f"{name}.json"
    cached = read_json(path, None)
    ttl = timedelta(minutes=ctx.settings.metrics_cache_minutes)
    if (
        cached and not force and cached.get("days") == days and cached.get("mode") == ctx.provider.mode
        and cached.get("region") == ctx.settings.region
        and utcnow() - datetime.fromisoformat(cached["fetched_at"]) < ttl
    ):
        return cached["metrics"]

    end = utcnow()
    start = end - timedelta(days=days)
    metrics = ctx.provider.get_metrics(name, start, end, 86400)
    metrics["max_memory_used_mb"] = ctx.provider.get_max_memory_used(name, start, end)
    metrics["summary"] = metrics_analyzer.summarize(metrics)
    fn_mem = None
    try:
        fn_mem = ctx.provider.get_function(name)["memory_mb"]
    except Exception:
        pass
    metrics["memory_utilization_pct"] = metrics_analyzer.memory_utilization_pct(
        metrics["max_memory_used_mb"], fn_mem or 0
    )
    write_json(path, {
        "fetched_at": end.isoformat(), "days": days, "mode": ctx.provider.mode,
        "region": ctx.settings.region, "metrics": metrics,
    })
    return metrics


def invalidate(ctx: Ctx, name: str) -> None:
    p = ctx.settings.data_dir / "metrics" / f"{name}.json"
    if p.exists():
        p.unlink()


def trimmed(metrics: dict) -> dict:
    """Drop the time series (used when storing baselines in audit records)."""
    return {k: v for k, v in metrics.items() if k != "series"}
