"""ONE shared boto3 session. No credentials are hardcoded anywhere.

Credentials come from the AWS CLI profile / environment / SSO, never from code.
"""
from __future__ import annotations

from functools import lru_cache

import boto3
from botocore.config import Config

BOTO_CONFIG = Config(
    retries={"max_attempts": 5, "mode": "standard"},
    connect_timeout=5,
    read_timeout=20,
    user_agent_extra="cloudcost-ai/1.0",
)


@lru_cache(maxsize=4)
def get_session(profile: str = "", region: str = "ap-south-1") -> boto3.Session:
    return boto3.Session(profile_name=profile or None, region_name=region)


def client(session: boto3.Session, service: str):
    return session.client(service, config=BOTO_CONFIG)


def clear_session_cache() -> None:
    get_session.cache_clear()
