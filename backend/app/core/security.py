import re
from pathlib import Path

from fastapi import HTTPException

# Lambda function names: letters, digits, hyphen, underscore, max 64 chars.
_FN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_REGION = re.compile(r"^[a-z]{2}(-[a-z]+)+-\d$")

ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]


def validate_function_name(name: str) -> str:
    if not _FN.match(name or ""):
        raise HTTPException(status_code=422, detail="Invalid Lambda function name.")
    return name


def validate_region(region: str) -> str:
    if not _REGION.match(region or ""):
        raise HTTPException(status_code=422, detail="Invalid AWS region.")
    return region


def safe_child(base: Path, filename: str) -> Path:
    """Resolve `filename` inside `base`, blocking path traversal."""
    p = (base / filename).resolve()
    if base.resolve() not in p.parents:
        raise HTTPException(status_code=400, detail="Invalid file name.")
    return p
