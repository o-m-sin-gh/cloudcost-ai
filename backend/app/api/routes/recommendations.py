from fastapi import APIRouter, Depends

from ...services import recommendation_service
from ...services.state import Ctx, get_ctx

router = APIRouter()


@router.get("/recommendations")
def recommendations(refresh: bool = False, ctx: Ctx = Depends(get_ctx)):
    return recommendation_service.build_analysis(ctx, force=refresh)


@router.get("/cost-analysis")
def cost_analysis(ctx: Ctx = Depends(get_ctx)):
    a = recommendation_service.build_analysis(ctx)
    rows = [
        {k: r[k] for k in ("function_name", "current_memory_mb", "recommended_memory_mb", "current_monthly_cost",
                           "recommended_monthly_cost", "monthly_savings", "annual_savings", "savings_source",
                           "savings_per_million_invocations", "status", "eligible")}
        for r in a["items"]
    ]
    return {"summary": a["summary"], "rows": rows,
            "disclaimer": "Costs are list-price estimates before the free allowance. Savings assume duration is unchanged unless AWS supplied the figure."}
