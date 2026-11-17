"""Shared helpers for the setup scripts. Run scripts from the project root."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.core.config import get_settings  # noqa: E402
from backend.app.aws.session import get_session  # noqa: E402

PREFIX = "cloudcost-demo-"
ROLE_NAME = "cloudcost-demo-role"
FUNCTIONS = {
    f"{PREFIX}light": {"memory": 1024, "timeout": 10},    # deliberately over-provisioned
    f"{PREFIX}compute": {"memory": 256, "timeout": 30},   # deliberately CPU-starved
}


def session():
    s = get_settings()
    return get_session(s.profile, s.region), s
