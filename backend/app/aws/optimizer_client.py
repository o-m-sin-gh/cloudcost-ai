"""AWS Compute Optimizer: read-only Lambda recommendations."""
from __future__ import annotations

from botocore.exceptions import ClientError

from engine.recommendation_analyzer import SOURCE_AWS

from .session import client


def _name_from_arn(arn: str) -> str:
    return arn.split(":function:")[1].split(":")[0]


def normalize_recommendation(r: dict) -> dict:
    options = sorted(r.get("memorySizeRecommendationOptions", []), key=lambda o: o.get("rank", 99))
    best = options[0] if options else None
    savings = None
    if best:
        v = best.get("savingsOpportunity", {}).get("estimatedMonthlySavings", {}).get("value")
        savings = float(v) if v is not None else None
    avg_ms = next(
        (m["value"] for m in r.get("utilizationMetrics", []) if m["name"] == "Duration" and m["statistic"] == "Average"),
        None,
    )
    return {
        "function_name": _name_from_arn(r["functionArn"]),
        "arn": r["functionArn"],
        "source": SOURCE_AWS,
        "finding": r.get("finding", "Unavailable"),                # Optimized | NotOptimized | Unavailable
        "reason_codes": r.get("findingReasonCodes", []),           # preserved exactly as AWS returned
        "current_memory_mb": r.get("currentMemorySize"),
        "recommended_memory_mb": best["memorySize"] if best else None,
        "number_of_invocations": r.get("numberOfInvocations"),
        "lookback_days": r.get("lookbackPeriodInDays"),
        "aws_monthly_savings_usd": savings,
        "performance_risk": r.get("currentPerformanceRisk"),
        "avg_duration_ms": avg_ms,
    }


class OptimizerGateway:
    def __init__(self, session):
        self.c = client(session, "compute-optimizer")

    def get_recommendations(self) -> dict:
        """Never raises for expected account states; returns a status instead."""
        try:
            status = self.c.get_enrollment_status().get("status")
        except ClientError as e:
            return self._error(e)
        if status != "Active":
            return {
                "status": "not_enrolled",
                "message": f"Compute Optimizer enrollment status is '{status}'. Opt in once in the AWS console, then wait for analysis.",
                "items": [],
            }
        items, token = [], None
        try:
            while True:
                kwargs = {"nextToken": token} if token else {}
                resp = self.c.get_lambda_function_recommendations(**kwargs)
                items.extend(normalize_recommendation(r) for r in resp.get("lambdaFunctionRecommendations", []))
                token = resp.get("nextToken")
                if not token:
                    break
        except ClientError as e:
            return self._error(e)
        return {"status": "ok", "message": f"{len(items)} recommendation(s) from AWS Compute Optimizer.", "items": items}

    @staticmethod
    def _error(e: ClientError) -> dict:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"].get("Message", "")
        if code in ("OptInRequiredException", "AccessDeniedException", "UnauthorizedOperation"):
            return {
                "status": "access_denied" if code != "OptInRequiredException" else "not_enrolled",
                "message": f"Compute Optimizer is not available for this identity/account ({code}). Using the labelled CloudCost fallback.",
                "items": [],
            }
        return {"status": "error", "message": f"{code}: {msg}", "items": []}
