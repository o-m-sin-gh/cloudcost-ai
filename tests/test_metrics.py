from datetime import datetime, timedelta, timezone

from botocore.exceptions import ClientError

from backend.app.aws.cloudwatch_client import CloudWatchGateway
from backend.app.services import metrics_service
from engine import metrics_analyzer

T0 = datetime(2026, 11, 1, tzinfo=timezone.utc)


class FakeCW:
    def get_metric_statistics(self, MetricName, **kw):
        d1, d2 = T0, T0 + timedelta(days=1)
        data = {
            "Invocations": [{"Timestamp": d1, "Sum": 100}, {"Timestamp": d2, "Sum": 300}],
            "Errors": [{"Timestamp": d1, "Sum": 2}],
            "Throttles": [],
            "Duration": [{"Timestamp": d1, "Average": 100, "Maximum": 400}, {"Timestamp": d2, "Average": 200, "Maximum": 900}],
            "ConcurrentExecutions": [{"Timestamp": d1, "Maximum": 4}],
        }
        return {"Datapoints": data[MetricName]}


class FakeLogs:
    def __init__(self, exc=None):
        self.exc = exc

    def filter_log_events(self, **kw):
        if self.exc:
            raise self.exc
        return {"events": [
            {"message": "REPORT RequestId: x Duration: 1 ms Max Memory Used: 54 MB"},
            {"message": "REPORT RequestId: y Duration: 1 ms Max Memory Used: 78 MB"},
        ]}


def _gw(logs=None):
    gw = CloudWatchGateway.__new__(CloudWatchGateway)
    gw.cw, gw.logs = FakeCW(), logs or FakeLogs()
    return gw


def test_weighted_average_duration_and_totals():
    m = _gw().get_metrics("f", T0, T0 + timedelta(days=2))
    assert m["invocations"] == 400 and m["errors"] == 2
    assert m["avg_duration_ms"] == 175.0          # (100*100 + 300*200) / 400
    assert m["max_duration_ms"] == 900 and m["max_concurrent"] == 4


def test_max_memory_used_parsed_from_report_lines():
    assert _gw().get_max_memory_used("f", T0, T0 + timedelta(days=1)) == 78


def test_missing_log_group_returns_none():
    err = ClientError({"Error": {"Code": "ResourceNotFoundException", "Message": "x"}}, "FilterLogEvents")
    assert _gw(FakeLogs(err)).get_max_memory_used("f", T0, T0 + timedelta(days=1)) is None


def test_no_history_gives_no_data_status():
    assert metrics_analyzer.summarize({"invocations": 0})["status"] == "no_data"


def test_metrics_cached_locally(ctx):
    a = metrics_service.get_function_metrics(ctx, "cloudcost-demo-light")
    assert (ctx.settings.data_dir / "metrics" / "cloudcost-demo-light.json").exists()
    b = metrics_service.get_function_metrics(ctx, "cloudcost-demo-light")
    assert a == b
