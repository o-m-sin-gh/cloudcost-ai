import pytest
from botocore.exceptions import NoCredentialsError

from backend.app.aws import provider as prov


class FakeSTS:
    def get_caller_identity(self):
        return {"Account": "123456789012", "Arn": "arn:aws:iam::123456789012:user/cloudcost"}


def _live(monkeypatch, sts):
    monkeypatch.setattr(prov, "get_session", lambda *a, **k: object())
    for g in ("LambdaGateway", "CloudWatchGateway", "OptimizerGateway"):
        monkeypatch.setattr(prov, g, lambda s: object())
    monkeypatch.setattr(prov, "client", lambda session, name: sts)
    return prov.LiveProvider("p", "ap-south-1")


def test_identity_ok(monkeypatch):
    ident = _live(monkeypatch, FakeSTS()).identity()
    assert ident["account_id"] == "123456789012" and ident["mode"] == "aws"


def test_missing_credentials_is_friendly(monkeypatch):
    class Boom:
        def get_caller_identity(self):
            raise NoCredentialsError()
    with pytest.raises(prov.ProviderError, match="aws configure"):
        _live(monkeypatch, Boom()).identity()
