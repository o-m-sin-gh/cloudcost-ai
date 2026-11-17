import pytest

from backend.app.services import optimization_service as svc


def _approved(ctx, name="cloudcost-demo-light"):
    rec = svc.dry_run(ctx, name, None)
    return svc.approve(ctx, rec["id"])


def test_approved_change_updates_memory_then_rollback_restores(ctx):
    rec = _approved(ctx)
    applied = svc.apply(ctx, rec["id"])
    assert applied["status"] == "applied" and applied["new_memory_mb"] == 256
    assert ctx.provider.get_function("cloudcost-demo-light")["memory_mb"] == 256
    assert applied["backup_file"]

    rolled = svc.rollback(ctx, rec["id"])
    assert rolled["status"] == "rolled_back"
    assert ctx.provider.get_function("cloudcost-demo-light")["memory_mb"] == 1024


def test_failed_update_is_recorded(ctx, monkeypatch):
    rec = _approved(ctx)
    def boom(name, mb): raise RuntimeError("AccessDenied")
    monkeypatch.setattr(ctx.provider, "update_memory", boom)
    out = svc.apply(ctx, rec["id"])
    assert out["status"] == "failed" and "AccessDenied" in out["error"]
    assert ctx.provider.get_function("cloudcost-demo-light")["memory_mb"] == 1024


def test_drift_is_detected(ctx):
    rec = _approved(ctx)
    ctx.provider.update_memory("cloudcost-demo-light", 512)   # someone changed it meanwhile
    with pytest.raises(svc.OptimizationError, match="drift"):
        svc.apply(ctx, rec["id"])


def test_real_aws_writes_blocked_by_default(ctx):
    rec = _approved(ctx)
    ctx.provider.mode = "aws"           # pretend we are on a live account
    ctx.settings.allow_writes = False
    with pytest.raises(svc.OptimizationError) as e:
        svc.apply(ctx, rec["id"])
    assert e.value.status_code == 403
    assert ctx.provider.get_function("cloudcost-demo-light")["memory_mb"] == 1024


def test_verify_compares_before_and_after(ctx):
    rec = _approved(ctx, "cloudcost-demo-compute")        # 256 -> 1024 (performance increase)
    svc.apply(ctx, rec["id"])
    v = svc.verify(ctx, rec["id"])["verification"]
    assert v["avg_duration_ms"]["after"] < v["avg_duration_ms"]["before"]
    assert v["verdict"] in {"faster_but_costlier", "improved"}


def test_history_has_audit_fields(ctx):
    rec = _approved(ctx)
    svc.apply(ctx, rec["id"])
    h = ctx.approvals.list()[0]
    for k in ("account_id", "region", "function_name", "old_memory_mb", "target_memory_mb",
              "new_memory_mb", "approved_at", "applied_at", "status", "api_result", "baseline_metrics"):
        assert k in h
