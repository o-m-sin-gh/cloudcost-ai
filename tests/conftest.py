import pytest

from backend.app.aws.demo import DemoProvider
from backend.app.core.config import Settings
from backend.app.services.state import Ctx


@pytest.fixture
def ctx(tmp_path):
    s = Settings(data_dir=tmp_path / "data", reports_dir=tmp_path / "reports")
    return Ctx(settings=s, provider=DemoProvider())
