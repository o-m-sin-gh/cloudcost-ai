from fastapi import APIRouter, Depends, Query

from ...core.security import validate_function_name
from ...services import metrics_service
from ...services.state import Ctx, get_ctx

router = APIRouter()


@router.get("/metrics/{function_name}")
def metrics(function_name: str, days: int = Query(14, ge=1, le=60), refresh: bool = False, ctx: Ctx = Depends(get_ctx)):
    validate_function_name(function_name)
    return metrics_service.get_function_metrics(ctx, function_name, days=days, force=refresh)
