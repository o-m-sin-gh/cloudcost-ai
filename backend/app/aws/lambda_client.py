from __future__ import annotations

from engine.inventory import normalize_function

from .session import client


class LambdaGateway:
    def __init__(self, session):
        self.c = client(session, "lambda")

    def list_functions(self) -> list[dict]:
        """Paginated: returns ALL functions, not just the first page."""
        out: list[dict] = []
        for page in self.c.get_paginator("list_functions").paginate():
            out.extend(normalize_function(f) for f in page.get("Functions", []))
        return out

    def get_function(self, name: str) -> dict:
        return normalize_function(self.c.get_function_configuration(FunctionName=name))

    def update_memory(self, name: str, memory_mb: int) -> dict:
        resp = self.c.update_function_configuration(FunctionName=name, MemorySize=int(memory_mb))
        # Wait until AWS finishes applying the update before reporting success.
        self.c.get_waiter("function_updated_v2").wait(FunctionName=name)
        fn = self.get_function(name)
        return {
            "request_id": resp.get("ResponseMetadata", {}).get("RequestId"),
            "memory_mb": fn["memory_mb"],
            "last_update_status": fn["last_update_status"],
        }
