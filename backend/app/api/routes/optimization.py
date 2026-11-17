from fastapi import APIRouter, Depends

from ...schemas.optimization_schema import DryRunRequest, RecordRequest
from ...services import optimization_service as svc
from ...services.state import Ctx, get_ctx

router = APIRouter(prefix="/optimization")


@router.post("/dry-run")
def dry_run(body: DryRunRequest, ctx: Ctx = Depends(get_ctx)):
    from ...core.security import validate_function_name
    validate_function_name(body.function_name)
    return svc.dry_run(ctx, body.function_name, body.target_memory_mb)


@router.post("/approve")
def approve(body: RecordRequest, ctx: Ctx = Depends(get_ctx)):
    return svc.approve(ctx, body.record_id)


@router.post("/reject")
def reject(body: RecordRequest, ctx: Ctx = Depends(get_ctx)):
    return svc.reject(ctx, body.record_id)


@router.post("/apply")
def apply(body: RecordRequest, ctx: Ctx = Depends(get_ctx)):
    return svc.apply(ctx, body.record_id)


@router.post("/verify")
def verify(body: RecordRequest, ctx: Ctx = Depends(get_ctx)):
    return svc.verify(ctx, body.record_id)


@router.post("/rollback")
def rollback(body: RecordRequest, ctx: Ctx = Depends(get_ctx)):
    return svc.rollback(ctx, body.record_id)


@router.get("/history")
def history(ctx: Ctx = Depends(get_ctx)):
    return ctx.approvals.list()
