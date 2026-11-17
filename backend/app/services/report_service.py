from __future__ import annotations

import csv
from pathlib import Path

from engine.store import write_json

from . import inventory_service, recommendation_service
from .state import Ctx

REPORT_FILES = [
    "inventory_report.csv", "metrics_report.csv", "recommendations.json",
    "savings_report.csv", "performance_comparison.csv",
]


def _csv(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def generate_all(ctx: Ctx) -> list[dict]:
    out = ctx.settings.reports_dir
    src = ctx.source_label
    inv = inventory_service.list_inventory(ctx)
    ana = recommendation_service.build_analysis(ctx)

    _csv(out / "inventory_report.csv",
         ["function", "runtime", "memory_mb", "timeout_s", "architecture", "state", "last_modified", "managed", "data_source"],
         [[f["name"], f["runtime"], f["memory_mb"], f["timeout_s"], f["architecture"], f["state"], f["last_modified"], f["managed"], src]
          for f in inv["functions"]])

    _csv(out / "metrics_report.csv",
         ["function", "invocations", "avg_duration_ms", "max_memory_used_mb", "finding", "status", "data_source"],
         [[r["function_name"], r["invocations"], r["avg_duration_ms"], r["max_memory_used_mb"], r["finding"], r["status"], src]
          for r in ana["items"]])

    write_json(out / "recommendations.json", {"data_source": src, **ana})

    _csv(out / "savings_report.csv",
         ["function", "current_mb", "recommended_mb", "current_monthly_cost_usd", "recommended_monthly_cost_usd",
          "monthly_savings_usd", "annual_savings_usd", "savings_source", "recommendation_source", "eligible"],
         [[r["function_name"], r["current_memory_mb"], r["recommended_memory_mb"], r["current_monthly_cost"],
           r["recommended_monthly_cost"], r["monthly_savings"], r["annual_savings"], r["savings_source"], r["source"], r["eligible"]]
          for r in ana["items"]])

    rows = []
    for rec in ctx.approvals.list():
        v = rec.get("verification") or {}
        if v.get("verdict") and v["verdict"] != "awaiting_data":
            rows.append([rec["function_name"], rec["old_memory_mb"], rec["new_memory_mb"],
                         v["avg_duration_ms"]["before"], v["avg_duration_ms"]["after"], v["avg_duration_ms"]["change_pct"],
                         v["cost_per_1000_invocations"]["change_pct"], v["verdict"], rec["status"]])
    _csv(out / "performance_comparison.csv",
         ["function", "old_mb", "new_mb", "avg_ms_before", "avg_ms_after", "duration_change_pct", "cost_change_pct", "verdict", "record_status"],
         rows)
    return list_reports(ctx)


def list_reports(ctx: Ctx) -> list[dict]:
    items = []
    for name in REPORT_FILES:
        p = ctx.settings.reports_dir / name
        items.append({"name": name, "exists": p.exists(), "size_bytes": p.stat().st_size if p.exists() else 0})
    return items
