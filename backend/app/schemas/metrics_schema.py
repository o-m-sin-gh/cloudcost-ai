from pydantic import BaseModel


class MetricPoint(BaseModel):
    ts: str
    invocations: float
    avg_duration_ms: float
    max_duration_ms: float
    errors: float
