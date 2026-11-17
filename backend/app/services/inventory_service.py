from __future__ import annotations

from engine.inventory import sort_inventory
from engine.store import write_json

from .state import Ctx, utcnow


def list_inventory(ctx: Ctx) -> dict:
    functions = sort_inventory(ctx.provider.list_functions())
    ident = ctx.provider.identity()
    payload = {
        "meta": {
            "account_id": ident["account_id"], "region": ident["region"], "mode": ctx.provider.mode,
            "fetched_at": utcnow().isoformat(timespec="seconds"), "count": len(functions),
            "managed_prefix": ctx.settings.managed_prefix,
        },
        "functions": [{**f, "managed": f["name"].startswith(ctx.settings.managed_prefix)} for f in functions],
    }
    write_json(ctx.settings.data_dir / "inventory" / "inventory.json", payload)
    return payload
