"""Approval-based optimization workflow: preview -> approve -> apply -> verify -> rollback."""
from __future__ import annotations

from datetime import datetime

from engine import configuration_backup, configuration_updater, optimization_rules, performance_comparator, rollback_manager
from engine.approval_manager import ApprovalError, now_iso

from . import metrics_service, recommendation_service
from .state import Ctx, utcnow


class OptimizationError(Exception):
    def __init__(self, message: str, status_code: int = 400, notes: list[str] | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.notes = notes or []


def _guard_writes(ctx: Ctx) -> None:
    if ctx.provider.mode == "aws" and not ctx.settings.allow_writes:
        raise OptimizationError(
            "Real AWS changes are disabled. Set allow_writes: true in config.yaml (or CLOUDCOST_ALLOW_WRITES=true) to enable them.",
            403,
        )


def _record(ctx: Ctx, record_id: str) -> dict:
    try:
        return ctx.approvals.get(record_id)
    except ApprovalError as e:
        raise OptimizationError(str(e), 404)


def dry_run(ctx: Ctx, function_name: str, target_memory_mb: int | None) -> dict:
    """Preview only. Never touches AWS configuration."""
    try:
        fn = ctx.provider.get_function(function_name)
    except Exception:
        raise OptimizationError(f"Function '{function_name}' was not found.", 404)

    analysis = recommendation_service.analysis_for(ctx, function_name)
    target = target_memory_mb or analysis.get("recommended_memory_mb")
    if not target:
        raise OptimizationError("No recommendation is available for this function; provide target_memory_mb.", 422, analysis.get("rule_notes"))

    savings = analysis.get("monthly_savings") if target == analysis.get("recommended_memory_mb") else None
    ok, notes = optimization_rules.validate_change(
        function_name=function_name, state=fn["state"], current_mb=fn["memory_mb"], target_mb=int(target),
        monthly_savings=savings, managed_prefix=ctx.settings.managed_prefix,
        min_monthly_savings=ctx.settings.min_monthly_savings_usd, max_reduction_pct=ctx.settings.max_reduction_pct,
    )
    if not ok:
        raise OptimizationError("Change blocked by safety rules.", 422, notes)

    baseline = metrics_service.trimmed(metrics_service.get_function_metrics(ctx, function_name))
    ident = ctx.provider.identity()
    return ctx.approvals.create(
        account_id=ident["account_id"], region=ident["region"], mode=ctx.provider.mode,
        function_name=function_name, architecture=fn["architecture"],
        old_memory_mb=fn["memory_mb"], recommended_memory_mb=analysis.get("recommended_memory_mb"),
        target_memory_mb=int(target), recommendation_source=analysis.get("source"),
        estimated_monthly_savings=savings, savings_source=analysis.get("savings_source"),
        rule_notes=notes, dry_run=configuration_updater.preview(fn, int(target)), baseline_metrics=baseline,
    )


def approve(ctx: Ctx, record_id: str) -> dict:
    _record(ctx, record_id)
    try:
        return ctx.approvals.transition(record_id, "approved", approved_at=now_iso())
    except ApprovalError as e:
        raise OptimizationError(str(e), 409)


def reject(ctx: Ctx, record_id: str) -> dict:
    _record(ctx, record_id)
    try:
        return ctx.approvals.transition(record_id, "rejected")
    except ApprovalError as e:
        raise OptimizationError(str(e), 409)


def apply(ctx: Ctx, record_id: str) -> dict:
    rec = _record(ctx, record_id)
    if rec["status"] != "approved":
        raise OptimizationError(f"Only approved records can be applied (this one is '{rec['status']}').", 409)
    _guard_writes(ctx)

    name = rec["function_name"]
    fn = ctx.provider.get_function(name)
    if fn["memory_mb"] != rec["old_memory_mb"]:
        raise OptimizationError(
            f"Configuration drift: memory is now {fn['memory_mb']} MB but the preview was made at {rec['old_memory_mb']} MB. Run a new dry-run.",
            409,
        )
    ok, notes = optimization_rules.validate_change(
        function_name=name, state=fn["state"], current_mb=fn["memory_mb"], target_mb=rec["target_memory_mb"],
        monthly_savings=rec.get("estimated_monthly_savings"), managed_prefix=ctx.settings.managed_prefix,
        min_monthly_savings=ctx.settings.min_monthly_savings_usd, max_reduction_pct=ctx.settings.max_reduction_pct,
    )
    if not ok:
        raise OptimizationError("Change blocked by safety rules.", 422, notes)

    backup = configuration_backup.save_backup(
        ctx.settings.data_dir / "backups", fn, record_id,
        {"account_id": rec["account_id"], "region": rec["region"], "saved_at": now_iso()},
    )
    try:
        result = configuration_updater.apply_memory(ctx.provider, name, rec["target_memory_mb"])
    except Exception as e:  # recorded in the audit trail, never swallowed
        return ctx.approvals.transition(record_id, "failed", backup_file=backup, error=str(e))
    metrics_service.invalidate(ctx, name)
    return ctx.approvals.transition(
        record_id, "applied", backup_file=backup, api_result=result,
        new_memory_mb=result["memory_mb"], applied_at=now_iso(),
    )


def rollback(ctx: Ctx, record_id: str) -> dict:
    rec = _record(ctx, record_id)
    if rec["status"] != "applied":
        raise OptimizationError(f"Only applied changes can be rolled back (this one is '{rec['status']}').", 409)
    _guard_writes(ctx)
    try:
        out = rollback_manager.rollback(ctx.provider, rec)
    except Exception as e:
        return ctx.approvals.update(record_id, error=f"Rollback failed: {e}")
    metrics_service.invalidate(ctx, rec["function_name"])
    return ctx.approvals.transition(
        record_id, "rolled_back", rollback={**out, "rolled_back_at": now_iso()}, error=None
    )


def verify(ctx: Ctx, record_id: str) -> dict:
    rec = _record(ctx, record_id)
    if rec["status"] != "applied" or not rec.get("applied_at"):
        raise OptimizationError("Only applied changes can be verified.", 409)
    name = rec["function_name"]
    start = datetime.fromisoformat(rec["applied_at"])
    after = metrics_service.trimmed(ctx.provider.get_metrics(name, start, utcnow(), 3600))
    cmp = performance_comparator.compare(
        rec["baseline_metrics"], after, rec["old_memory_mb"], rec["new_memory_mb"],
        rec.get("architecture", "x86_64"), ctx.settings.pricing,
        min_invocations=5,
    )
    cmp["checked_at"] = now_iso()
    cmp["data_source"] = "demo (simulated)" if ctx.provider.mode == "demo" else "aws-cloudwatch"
    return ctx.approvals.update(record_id, verification=cmp)
