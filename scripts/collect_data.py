"""Save inventory / metrics / recommendations snapshots and CSV+JSON reports locally.  python scripts/collect_data.py"""
from _common import ROOT  # noqa: F401  (sets sys.path)
from backend.app.core.config import get_settings
from backend.app.aws.provider import get_provider
from backend.app.services import report_service
from backend.app.services.state import Ctx

s = get_settings()
ctx = Ctx(settings=s, provider=get_provider(s))
print(f"Mode: {s.mode}  Region: {s.region}")
for r in report_service.generate_all(ctx):
    print(("  wrote " if r["exists"] else "  MISSING ") + r["name"])
