"""Single access point for cloud data. Two implementations share one interface:

  LiveProvider  - real AWS via the shared boto3 session (mode: aws)
  DemoProvider  - built-in sample data, no AWS needed   (mode: demo)

Nothing else in the app imports boto3 directly.
"""
from __future__ import annotations

from datetime import datetime

from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError, ProfileNotFound

from .cloudwatch_client import CloudWatchGateway
from .lambda_client import LambdaGateway
from .optimizer_client import OptimizerGateway
from .session import client, get_session


class ProviderError(Exception):
    """A user-facing AWS problem (bad credentials, missing permission, ...)."""


def _wrap(fn):
    def inner(*a, **k):
        try:
            return fn(*a, **k)
        except NoCredentialsError:
            raise ProviderError("No AWS credentials found. Run `aws configure` (or `aws configure sso`) and set AWS_PROFILE.")
        except ProfileNotFound as e:
            raise ProviderError(str(e))
        except ClientError as e:
            err = e.response["Error"]
            raise ProviderError(f"AWS error {err.get('Code')}: {err.get('Message')}")
        except BotoCoreError as e:
            raise ProviderError(f"AWS connection problem: {e}")
    return inner


class LiveProvider:
    mode = "aws"

    def __init__(self, profile: str, region: str):
        self.region = region
        self.session = get_session(profile, region)
        self.lambda_ = LambdaGateway(self.session)
        self.cw = CloudWatchGateway(self.session)
        self.optimizer = OptimizerGateway(self.session)

    @_wrap
    def identity(self) -> dict:
        who = client(self.session, "sts").get_caller_identity()
        return {"account_id": who["Account"], "arn": who["Arn"], "region": self.region, "mode": "aws"}

    @_wrap
    def list_functions(self) -> list[dict]:
        return self.lambda_.list_functions()

    @_wrap
    def get_function(self, name: str) -> dict:
        return self.lambda_.get_function(name)

    @_wrap
    def get_metrics(self, name: str, start: datetime, end: datetime, period: int = 86400) -> dict:
        return self.cw.get_metrics(name, start, end, period)

    @_wrap
    def get_max_memory_used(self, name: str, start: datetime, end: datetime) -> int | None:
        return self.cw.get_max_memory_used(name, start, end)

    @_wrap
    def get_recommendations(self) -> dict:
        return self.optimizer.get_recommendations()

    @_wrap
    def update_memory(self, name: str, memory_mb: int) -> dict:
        return self.lambda_.update_memory(name, memory_mb)


_cache: dict[tuple, object] = {}


def get_provider(settings):
    key = (settings.mode, settings.profile, settings.region)
    if key not in _cache:
        if settings.mode == "aws":
            _cache[key] = LiveProvider(settings.profile, settings.region)
        else:
            from .demo import DemoProvider
            _cache[key] = DemoProvider()
    return _cache[key]


def clear_provider_cache() -> None:
    _cache.clear()
