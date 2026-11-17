from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services import report_service
from backend.app.services.state import get_ctx


def test_reports_generated(ctx):
    report_service.generate_all(ctx)
    for name in report_service.REPORT_FILES:
        assert (ctx.settings.reports_dir / name).exists(), name
    head = (ctx.settings.reports_dir / "savings_report.csv").read_text().splitlines()[0]
    assert "savings_source" in head


def test_api_smoke_and_path_traversal(ctx):
    app.dependency_overrides[get_ctx] = lambda: ctx
    try:
        c = TestClient(app)
        assert c.get("/api/health").json() == {"status": "ok"}
        assert c.get("/api/aws/connection").json()["mode"] == "demo"
        assert len(c.get("/api/lambda/functions").json()["functions"]) == 7
        assert c.get("/api/lambda/bad name!").status_code in (404, 422)
        assert c.get("/api/reports/..%2F..%2Fconfig.yaml").status_code in (400, 404)
        r = c.post("/api/optimization/dry-run", json={"function_name": "cloudcost-demo-light"})
        assert r.status_code == 200 and r.json()["status"] == "previewed"
        assert c.post("/api/optimization/dry-run", json={"function_name": "orders-prod-processor", "target_memory_mb": 256}).status_code == 422
    finally:
        app.dependency_overrides.clear()
