from backend.app.aws.lambda_client import LambdaGateway
from backend.app.services import inventory_service


class FakePaginator:
    def paginate(self):
        yield {"Functions": [{"FunctionName": "a", "MemorySize": 128}, {"FunctionName": "b", "MemorySize": 256}]}
        yield {"Functions": [{"FunctionName": "c", "MemorySize": 512, "Architectures": ["arm64"]}]}


class FakeLambda:
    def get_paginator(self, name):
        assert name == "list_functions"
        return FakePaginator()


def test_pagination_returns_all_pages():
    gw = LambdaGateway.__new__(LambdaGateway)
    gw.c = FakeLambda()
    fns = gw.list_functions()
    assert [f["name"] for f in fns] == ["a", "b", "c"]
    assert fns[2]["architecture"] == "arm64" and fns[0]["architecture"] == "x86_64"


def test_inventory_flags_managed_scope(ctx):
    inv = inventory_service.list_inventory(ctx)
    managed = {f["name"]: f["managed"] for f in inv["functions"]}
    assert managed["cloudcost-demo-light"] is True
    assert managed["orders-prod-processor"] is False
    assert (ctx.settings.data_dir / "inventory" / "inventory.json").exists()
