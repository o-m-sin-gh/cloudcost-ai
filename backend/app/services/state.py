"""Shared per-request context: settings + provider + approval store."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from engine.approval_manager import ApprovalManager

from ..aws.provider import get_provider
from ..core.config import Settings, get_settings


@dataclass
class Ctx:
    settings: Settings
    provider: object

    @property
    def approvals(self) -> ApprovalManager:
        return ApprovalManager(self.settings.data_dir / "history")

    @property
    def source_label(self) -> str:
        return "demo" if self.provider.mode == "demo" else "aws"


def get_ctx() -> Ctx:
    s = get_settings()
    return Ctx(settings=s, provider=get_provider(s))


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
