import os
from enum import StrEnum

DB_PATH_ENV = "WORKSHOP_DB_PATH"
UPLOAD_DIR_ENV = "WORKSHOP_UPLOAD_DIR"
AUTH_HEALTH_URL_ENV = "AUTH_HEALTH_URL"

DEFAULT_DB_PATH = "./data/workshop.db"
DEFAULT_UPLOAD_DIR = "./uploads"
DEFAULT_AUTH_HEALTH_URL = "http://localhost:8080/q/health"
HEALTH_TIMEOUT_SECONDS = 3.0
HEALTH_UNAVAILABLE_STATUS = 0
HEALTH_UNAVAILABLE_MESSAGE = "Auth service unavailable"

CORS_ORIGINS_ENV = "WORKSHOP_CORS_ORIGINS"
DEFAULT_CORS_ORIGINS = "http://localhost:4200"
CORS_ORIGIN_SEPARATOR = ","
CORS_ALLOWED_METHODS = ("GET", "POST")
CORS_ALLOWED_HEADERS = ("Authorization", "Content-Type")

TITLE_MAX_LENGTH = 200
DESCRIPTION_MAX_LENGTH = 2000


class TaskStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    ARCHIVED = "ARCHIVED"


class TaskPriority(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


DEFAULT_STATUS = TaskStatus.TODO
DEFAULT_PRIORITY = TaskPriority.MEDIUM
HIGH_PRIORITY = TaskPriority.HIGH
CLOSED_STATUSES = frozenset({TaskStatus.DONE, TaskStatus.ARCHIVED})


def db_path() -> str:
    return os.getenv(DB_PATH_ENV, DEFAULT_DB_PATH)


def upload_dir() -> str:
    return os.getenv(UPLOAD_DIR_ENV, DEFAULT_UPLOAD_DIR)


def auth_health_url() -> str:
    return os.getenv(AUTH_HEALTH_URL_ENV, DEFAULT_AUTH_HEALTH_URL)


def cors_origins() -> list[str]:
    raw_origins = os.getenv(CORS_ORIGINS_ENV, DEFAULT_CORS_ORIGINS)
    return [origin.strip() for origin in raw_origins.split(CORS_ORIGIN_SEPARATOR) if origin.strip()]
