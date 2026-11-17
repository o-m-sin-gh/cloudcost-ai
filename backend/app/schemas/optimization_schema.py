from pydantic import BaseModel, Field


class DryRunRequest(BaseModel):
    function_name: str
    target_memory_mb: int | None = Field(default=None, ge=128, le=10240)


class RecordRequest(BaseModel):
    record_id: str = Field(min_length=4, max_length=40)
