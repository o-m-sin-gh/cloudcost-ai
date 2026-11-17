from pydantic import BaseModel


class SettingsUpdate(BaseModel):
    region: str | None = None
    lookback_days: int | None = None
    min_monthly_savings_usd: float | None = None
