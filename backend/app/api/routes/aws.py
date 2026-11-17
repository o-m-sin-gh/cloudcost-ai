from fastapi import APIRouter, Depends

from engine.store import read_json, write_json

from ...aws.provider import clear_provider_cache
from ...core import config
from ...core.security import validate_region
from ...schemas.lambda_schema import SettingsUpdate
from ...services.state import Ctx, get_ctx, utcnow

router = APIRouter()


@router.get("/aws/connection")
def connection(ctx: Ctx = Depends(get_ctx)):
    ident = ctx.provider.identity()
    path = ctx.settings.data_dir / "last_connection.json"
    now = utcnow().isoformat(timespec="seconds")
    previous = read_json(path, {}).get("last_success")
    write_json(path, {"last_success": now})
    return {
        "connected": True, "mode": ctx.provider.mode, **ident,
        "last_successful_connection": now, "previous_successful_connection": previous,
        "writes_enabled": ctx.settings.allow_writes or ctx.provider.mode == "demo",
        "managed_prefix": ctx.settings.managed_prefix,
    }


@router.get("/settings")
def get_settings_route(ctx: Ctx = Depends(get_ctx)):
    return ctx.settings.public()


@router.put("/settings")
def update_settings(body: SettingsUpdate, ctx: Ctx = Depends(get_ctx)):
    changes = body.model_dump(exclude_none=True)
    if "region" in changes:
        validate_region(changes["region"])
    if "lookback_days" in changes and not (1 <= changes["lookback_days"] <= 60):
        from fastapi import HTTPException
        raise HTTPException(422, "lookback_days must be between 1 and 60.")
    s = config.update_editable(changes)
    clear_provider_cache()
    return s.public()
