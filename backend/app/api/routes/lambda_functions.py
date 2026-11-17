from fastapi import APIRouter, Depends, HTTPException

from ...core.security import validate_function_name
from ...services import inventory_service, metrics_service, recommendation_service
from ...services.state import Ctx, get_ctx

router = APIRouter()


@router.get("/lambda/functions")
def functions(ctx: Ctx = Depends(get_ctx)):
    return inventory_service.list_inventory(ctx)


@router.get("/lambda/{function_name}")
def function_detail(function_name: str, ctx: Ctx = Depends(get_ctx)):
    validate_function_name(function_name)
    try:
        fn = ctx.provider.get_function(function_name)
    except Exception:
        raise HTTPException(404, f"Function '{function_name}' not found.")
    metrics = metrics_service.get_function_metrics(ctx, function_name)
    try:
        analysis = recommendation_service.analysis_for(ctx, function_name)
    except KeyError:
        analysis = None
    return {"function": fn, "metrics": metrics, "analysis": analysis, "data_source": ctx.source_label}
