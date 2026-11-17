from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from ...core.security import safe_child
from ...services import report_service
from ...services.state import Ctx, get_ctx

router = APIRouter()


@router.get("/reports")
def list_reports(ctx: Ctx = Depends(get_ctx)):
    return report_service.list_reports(ctx)


@router.post("/reports/generate")
def generate(ctx: Ctx = Depends(get_ctx)):
    return report_service.generate_all(ctx)


@router.get("/reports/{name}")
def download(name: str, ctx: Ctx = Depends(get_ctx)):
    if name not in report_service.REPORT_FILES:
        raise HTTPException(404, "Unknown report.")
    path = safe_child(ctx.settings.reports_dir, name)
    if not path.exists():
        raise HTTPException(404, "Report not generated yet. Click Generate first.")
    return FileResponse(path, filename=name)
