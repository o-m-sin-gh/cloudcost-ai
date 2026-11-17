import pytest

from backend.app.services import optimization_service as svc


def test_dry_run_changes_nothing(ctx):
    before = ctx.provider.get_function("cloudcost-demo-light")["memory_mb"]
    rec = svc.dry_run(ctx, "cloudcost-demo-light", None)
    assert rec["status"] == "previewed" and rec["dry_run"]["dry_run"] is True
    assert rec["target_memory_mb"] == 256 and rec["old_memory_mb"] == before
    assert ctx.provider.get_function("cloudcost-demo-light")["memory_mb"] == before


def test_dry_run_blocked_outside_scope(ctx):
    with pytest.raises(svc.OptimizationError) as e:
        svc.dry_run(ctx, "orders-prod-processor", 256)
    assert e.value.status_code == 422 and any("managed scope" in n for n in e.value.notes)


def test_dry_run_blocks_excessive_reduction(ctx):
    with pytest.raises(svc.OptimizationError) as e:
        svc.dry_run(ctx, "cloudcost-demo-light", 128)   # 1024 -> 128 = 87.5% cut
    assert any("single-step limit" in n for n in e.value.notes)


def test_dry_run_unknown_function(ctx):
    with pytest.raises(svc.OptimizationError) as e:
        svc.dry_run(ctx, "does-not-exist", 256)
    assert e.value.status_code == 404


def test_cannot_apply_without_approval(ctx):
    rec = svc.dry_run(ctx, "cloudcost-demo-light", None)
    with pytest.raises(svc.OptimizationError) as e:
        svc.apply(ctx, rec["id"])
    assert e.value.status_code == 409


def test_reject_is_terminal(ctx):
    rec = svc.dry_run(ctx, "cloudcost-demo-light", None)
    svc.reject(ctx, rec["id"])
    with pytest.raises(svc.OptimizationError):
        svc.approve(ctx, rec["id"])
