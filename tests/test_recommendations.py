from botocore.exceptions import ClientError

from backend.app.aws.optimizer_client import OptimizerGateway, normalize_recommendation
from backend.app.services import recommendation_service
from engine import recommendation_analyzer as ra

RULES = {"managed_prefix": "cloudcost-demo-", "min_monthly_savings_usd": 0.0, "max_reduction_pct": 75}
FN = {"name": "cloudcost-demo-light", "arn": "arn", "memory_mb": 1024, "architecture": "x86_64", "state": "Active"}
METRICS = {"invocations": 1400, "period_days": 14, "avg_duration_ms": 100.0}

AWS_PAYLOAD = {
    "functionArn": "arn:aws:lambda:ap-south-1:123456789012:function:cloudcost-demo-light:$LATEST",
    "currentMemorySize": 1024, "finding": "NotOptimized", "findingReasonCodes": ["MemoryOverprovisioned"],
    "numberOfInvocations": 1400, "lookbackPeriodInDays": 14,
    "utilizationMetrics": [{"name": "Duration", "statistic": "Average", "value": 100.0}],
    "memorySizeRecommendationOptions": [
        {"rank": 2, "memorySize": 512},
        {"rank": 1, "memorySize": 256, "savingsOpportunity": {"estimatedMonthlySavings": {"currency": "USD", "value": 0.0021}}},
    ],
}


def test_aws_payload_preserves_finding_and_reason_codes():
    r = normalize_recommendation(AWS_PAYLOAD)
    assert r["function_name"] == "cloudcost-demo-light"
    assert r["finding"] == "NotOptimized" and r["reason_codes"] == ["MemoryOverprovisioned"]
    assert r["recommended_memory_mb"] == 256 and r["aws_monthly_savings_usd"] == 0.0021
    assert r["source"] == "aws-compute-optimizer"


def test_aws_savings_are_used_and_labelled_aws():
    row = ra.analyze(FN, METRICS, normalize_recommendation(AWS_PAYLOAD), RULES)
    assert row["savings_source"] == "aws" and row["monthly_savings"] == 0.0021
    assert row["annual_savings"] == round(12 * 0.0021, 8) and row["eligible"] is True


def test_estimated_savings_when_aws_gives_none():
    rec = {**normalize_recommendation(AWS_PAYLOAD), "aws_monthly_savings_usd": None}
    row = ra.analyze(FN, METRICS, rec, RULES)
    assert row["savings_source"] == "estimated" and row["monthly_savings"] > 0


def test_unavailable_is_awaiting_data_not_invented_savings():
    rec = {"finding": "Unavailable", "reason_codes": ["InsufficientData"], "source": "aws-compute-optimizer"}
    row = ra.analyze(FN, METRICS, rec, RULES)
    assert row["status"] == "awaiting_data" and row["monthly_savings"] is None and row["savings_source"] == "none"


def test_no_recommendation_graceful_empty_state():
    row = ra.analyze(FN, METRICS, None, RULES)
    assert row["status"] == "awaiting_data" and row["recommended_memory_mb"] is None


def test_outside_managed_scope_not_eligible():
    fn = {**FN, "name": "orders-prod-processor"}
    row = ra.analyze(fn, METRICS, normalize_recommendation(AWS_PAYLOAD), RULES)
    assert row["eligible"] is False and any("managed scope" in n for n in row["rule_notes"])


def test_heuristic_is_labelled_and_needs_data():
    h = ra.heuristic_recommendation(FN, {"invocations": 5}, 80)
    assert h["finding"] == "Unavailable" and h["source"] == "cloudcost-heuristic"
    h = ra.heuristic_recommendation(FN, {"invocations": 500}, 80)
    assert h["finding"] == "NotOptimized" and h["recommended_memory_mb"] == 128 and h["source"] == "cloudcost-heuristic"


def _gateway(exc=None, status="Active"):
    class C:
        def get_enrollment_status(self):
            if exc: raise exc
            return {"status": status}
        def get_lambda_function_recommendations(self, **kw):
            return {"lambdaFunctionRecommendations": [AWS_PAYLOAD]}
    g = OptimizerGateway.__new__(OptimizerGateway)
    g.c = C()
    return g


def test_optimizer_ok():
    r = _gateway().get_recommendations()
    assert r["status"] == "ok" and len(r["items"]) == 1


def test_optimizer_not_enrolled():
    assert _gateway(status="Inactive").get_recommendations()["status"] == "not_enrolled"


def test_optimizer_access_denied_falls_back_gracefully():
    err = ClientError({"Error": {"Code": "AccessDeniedException", "Message": "no"}}, "GetEnrollmentStatus")
    r = _gateway(exc=err).get_recommendations()
    assert r["status"] == "access_denied" and r["items"] == []


def test_analysis_over_demo_data(ctx):
    a = recommendation_service.build_analysis(ctx)
    by = {r["function_name"]: r for r in a["items"]}
    assert by["cloudcost-demo-light"]["status"] == "opportunity"
    assert by["cloudcost-demo-compute"]["status"] == "increase_suggested"
    assert by["cloudcost-demo-api-handler"]["status"] == "optimized"
    assert by["cloudcost-demo-image-resizer"]["status"] == "awaiting_data"   # >1792 MB -> Inconclusive
    assert by["orders-prod-processor"]["eligible"] is False
    assert a["summary"]["data_source"] == "demo"
