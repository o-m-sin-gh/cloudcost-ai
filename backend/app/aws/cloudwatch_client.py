"""CloudWatch access.

Uses GetMetricStatistics (inside the CloudWatch free API allowance) instead of
GetMetricData, which AWS always bills. Logs are read with FilterLogEvents.
"""
from __future__ import annotations

import re
from datetime import datetime

from botocore.exceptions import ClientError

from .session import client

_MEM = re.compile(r"Max Memory Used:\s*(\d+)\s*MB")


class CloudWatchGateway:
    def __init__(self, session):
        self.cw = client(session, "cloudwatch")
        self.logs = client(session, "logs")

    def _stat(self, name: str, metric: str, start: datetime, end: datetime, period: int, stats: list[str]):
        resp = self.cw.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName=metric,
            Dimensions=[{"Name": "FunctionName", "Value": name}],
            StartTime=start,
            EndTime=end,
            Period=period,
            Statistics=stats,
        )
        return {p["Timestamp"]: p for p in resp.get("Datapoints", [])}

    def get_metrics(self, name: str, start: datetime, end: datetime, period: int = 86400) -> dict:
        inv = self._stat(name, "Invocations", start, end, period, ["Sum"])
        err = self._stat(name, "Errors", start, end, period, ["Sum"])
        thr = self._stat(name, "Throttles", start, end, period, ["Sum"])
        dur = self._stat(name, "Duration", start, end, period, ["Average", "Maximum"])
        con = self._stat(name, "ConcurrentExecutions", start, end, period, ["Maximum"])

        series, total_inv, weighted = [], 0.0, 0.0
        for ts in sorted(set(inv) | set(dur)):
            n = inv.get(ts, {}).get("Sum", 0.0)
            avg = dur.get(ts, {}).get("Average", 0.0)
            total_inv += n
            weighted += n * avg
            series.append({
                "ts": ts.isoformat(),
                "invocations": n,
                "avg_duration_ms": round(avg, 2),
                "max_duration_ms": round(dur.get(ts, {}).get("Maximum", 0.0), 2),
                "errors": err.get(ts, {}).get("Sum", 0.0),
            })
        return {
            "function": name,
            "source": "aws-cloudwatch",
            "period_days": round((end - start).total_seconds() / 86400, 3),
            "invocations": int(total_inv),
            "errors": int(sum(p["Sum"] for p in err.values())),
            "throttles": int(sum(p["Sum"] for p in thr.values())),
            "avg_duration_ms": round(weighted / total_inv, 2) if total_inv else 0.0,
            "max_duration_ms": round(max((p["Maximum"] for p in dur.values()), default=0.0), 2),
            "max_concurrent": int(max((p["Maximum"] for p in con.values()), default=0)),
            "series": series,
        }

    def get_max_memory_used(self, name: str, start: datetime, end: datetime, max_events: int = 400) -> int | None:
        """Parse 'Max Memory Used' from Lambda REPORT log lines (not a standard metric)."""
        best, seen, token = None, 0, None
        try:
            while seen < max_events:
                kwargs = dict(
                    logGroupName=f"/aws/lambda/{name}",
                    startTime=int(start.timestamp() * 1000),
                    endTime=int(end.timestamp() * 1000),
                    filterPattern='"REPORT RequestId"',
                    limit=100,
                )
                if token:
                    kwargs["nextToken"] = token
                resp = self.logs.filter_log_events(**kwargs)
                for ev in resp.get("events", []):
                    seen += 1
                    m = _MEM.search(ev["message"])
                    if m:
                        best = max(best or 0, int(m.group(1)))
                token = resp.get("nextToken")
                if not token:
                    break
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                return None  # function never ran, so no log group yet
            raise
        return best
