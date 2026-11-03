import base64
import logging
import time
from typing import TypedDict

from fastapi import Header, HTTPException

logger = logging.getLogger(__name__)

LEGACY_SECRET = "WORKSHOP_SECRET_2026"
BEARER_PREFIX = "Bearer "
TOKEN_FIELD_SEPARATOR = "|"
TOKEN_FIELD_COUNT = 4
INVALID_TOKEN_ERROR = "invalid token"
INVALID_TOKEN_DETAIL = "Invalid token"
UNAUTHORIZED = 401


class Identity(TypedDict):
    username: str
    role: str


def decode_legacy_token(authorization: str) -> Identity:
    token = authorization.replace(BEARER_PREFIX, "")
    fields = base64.b64decode(token).decode("utf-8").split(TOKEN_FIELD_SEPARATOR)
    if len(fields) != TOKEN_FIELD_COUNT:
        raise ValueError(INVALID_TOKEN_ERROR)
    username, role, expires_at, secret = fields
    if secret != LEGACY_SECRET or int(expires_at) < int(time.time()):
        raise ValueError(INVALID_TOKEN_ERROR)
    return Identity(username=username, role=role)


def legacy_identity(authorization: str = Header(default="")) -> Identity:
    try:
        return decode_legacy_token(authorization)
    except ValueError as error:
        logger.warning("Rejected invalid token: %s", error)
        raise HTTPException(status_code=UNAUTHORIZED, detail=INVALID_TOKEN_DETAIL) from error
