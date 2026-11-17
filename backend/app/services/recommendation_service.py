from __future__ import annotations

from engine import recommendation_analyzer as ra
from engine.store import write_json

from . import metrics_service
from .state import Ctx, utcnow

MAX_ANALYZED = 50  # keeps CloudWatch API usage bounded on large accounts


def build_analysis(ctx: Ctx, force: bool = False) -> dict:
    functions = ctx.provider.list_functions()[:MAX_ANALYZED]
    optimizer = ctx.provider.get_recommendations()
    by_name = {r["function_name"]: r for r in optimizer["items"]}

    rows = []
    for fn in functions:
        metrics = metrics_service.get_function_metrics(ctx, fn["name"], force=force)
        rec = by_name.get(fn["name"])
        if rec is None:
            # Compute Optimizer gave nothing for this function (or is unavailable):
            # use our own heuristic. It is always labelled source="cloudcost-heuristic".
            rec = ra.heuristic_recommendation(fn, metrics, metrics.get("max_memory_used_mb"))
        row = ra.analyze(fn, metrics, rec, ctx.settings.rules(), ctx.settings.pricing)
        row.update(
            architecture=fn["architecture"], runtime=fn["runtime"],
            avg_duration_ms=metrics.get("avg_duration_ms"), invocations=metrics.get("invocations"),
            max_memory_used_mb=metrics.get("max_memory_used_mb"),
            data_source=ctx.source_label,
            managed=fn["name"].startswith(ctx.settings.managed_prefix),
        )
        rows.append(row)

    opportunities = [r for r in rows if r["status"] == "opportunity"]
    eligible = [r for r in opportunities if r["eligible"]]
    out_of_scope = [r for r in opportunities if not r["eligible"]]
    summary = {
        "total_functions": len(functions),
        "analysed": sum(1 for r in rows if r["finding"] != "Unavailable"),
        "opportunities": len(eligible),
        "opportunities_out_of_scope": len(out_of_scope),
        "potential_monthly_savings": round(sum(r["monthly_savings"] or 0 for r in eligible), 8),
        "potential_annual_savings": round(sum(r["annual_savings"] or 0 for r in eligible), 8),
        "savings_at_1m_invocations": round(sum(r["savings_per_million_invocations"] or 0 for r in eligible), 4),
        "data_source": ctx.source_label,
        "savings_label": "estimated" if ctx.provider.mode == "aws" else "illustrative (demo data)",
    }
    payload = {
        "generated_at": utcnow().isoformat(timespec="seconds"),
        "optimizer": {"status": optimizer["status"], "message": optimizer["message"]},
        "summary": summary,
        "items": rows,
    }
    write_json(ctx.settings.data_dir / "recommendations" / "analysis.json", payload)
    return payload


def analysis_for(ctx: Ctx, name: str) -> dict:
    for r in build_analysis(ctx)["items"]:
        if r["function_name"] == name:
            return r
    raise KeyError(name)
