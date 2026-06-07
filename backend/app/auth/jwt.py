from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.config.settings import settings


def create_access_token(payload: dict[str, Any]) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=settings.jwt_exp_seconds)
    token_payload = {**payload, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    return jwt.encode(token_payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])

