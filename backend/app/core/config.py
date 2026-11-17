from __future__ import annotations

import os
from dataclasses import dataclass, field, asdict
from pathlib import Path

import yaml

from engine.savings_calculator import DEFAULT_PRICING
from engine.store import read_json, write_json

ROOT = Path(__file__).resolve().parents[3]
EDITABLE = {"region": str, "lookback_days": int, "min_monthly_savings_usd": float}


def _load_dotenv() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


@dataclass
class Settings:
    mode: str = "demo"
    region: str = "ap-south-1"
    profile: str = ""
    lookback_days: int = 14
    metrics_cache_minutes: int = 10
    allow_writes: bool = False
    managed_prefix: str = "cloudcost-demo-"
    max_reduction_pct: float = 75.0
    min_monthly_savings_usd: float = 0.0
    pricing: dict = field(default_factory=lambda: DEFAULT_PRICING)
    data_dir: Path = ROOT / "data"
    reports_dir: Path = ROOT / "reports"

    def rules(self) -> dict:
        return {
            "managed_prefix": self.managed_prefix,
            "min_monthly_savings_usd": self.min_monthly_savings_usd,
            "max_reduction_pct": self.max_reduction_pct,
        }

    def public(self) -> dict:
        d = asdict(self)
        d.pop("data_dir"); d.pop("reports_dir")
        return d


def load_settings(root: Path = ROOT) -> Settings:
    _load_dotenv()
    s = Settings(data_dir=root / "data", reports_dir=root / "reports")
    cfg_path = root / "config.yaml"
    if cfg_path.exists():
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        for k, v in cfg.items():
            if hasattr(s, k):
                setattr(s, k, v)
    # UI overrides (region / lookback / threshold only)
    for k, v in read_json(s.data_dir / "settings.json", {}).items():
        if k in EDITABLE:
            setattr(s, k, v)
    # Environment overrides
    s.mode = os.environ.get("CLOUDCOST_MODE", s.mode).lower()
    s.region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", s.region))
    s.profile = os.environ.get("AWS_PROFILE", s.profile)
    if "CLOUDCOST_ALLOW_WRITES" in os.environ:
        s.allow_writes = os.environ["CLOUDCOST_ALLOW_WRITES"].lower() == "true"
    return s


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def update_editable(changes: dict) -> Settings:
    s = get_settings()
    saved = read_json(s.data_dir / "settings.json", {})
    for k, v in changes.items():
        if k in EDITABLE and v is not None:
            v = EDITABLE[k](v)
            setattr(s, k, v)
            saved[k] = v
    write_json(s.data_dir / "settings.json", saved)
    return s


def reset_settings() -> None:
    global _settings
    _settings = None
