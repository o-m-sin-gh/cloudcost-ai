"""CloudCost AI backend. Run from the project root:

    uvicorn backend.app.main:app --port 8000
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routes import aws, health, lambda_functions, metrics, optimization, recommendations, reports
from .aws.provider import ProviderError
from .core.logging import setup_logging
from .core.security import ALLOWED_ORIGINS
from .services.optimization_service import OptimizationError

setup_logging()
app = FastAPI(title="CloudCost AI", version="1.0.0", description="Local application API (not AWS API Gateway).")

app.add_middleware(
    CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_methods=["GET", "POST", "PUT"], allow_headers=["Content-Type"],
)

for r in (health, aws, lambda_functions, metrics, recommendations, optimization, reports):
    app.include_router(r.router, prefix="/api")


@app.exception_handler(ProviderError)
async def provider_error(_: Request, exc: ProviderError):
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.exception_handler(OptimizationError)
async def optimization_error(_: Request, exc: OptimizationError):
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc), "notes": exc.notes})
