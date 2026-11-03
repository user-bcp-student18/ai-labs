import logging
from collections import Counter
from pathlib import Path

import urllib3

from app.config import (
    CLOSED_STATUSES,
    HEALTH_TIMEOUT_SECONDS,
    HEALTH_UNAVAILABLE_MESSAGE,
    HEALTH_UNAVAILABLE_STATUS,
    HIGH_PRIORITY,
    auth_health_url,
)
from app.repository import TaskRepository
from app.schemas import SummaryResponse, TaskCreate, TaskResponse
from app.security import Identity

logger = logging.getLogger(__name__)


def resolve_owner(requested_owner: str | None, identity: Identity) -> str:
    return requested_owner or identity["username"]


def is_high_priority_open(status: str, priority: str) -> bool:
    return priority == HIGH_PRIORITY and status not in CLOSED_STATUSES


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def list_tasks(self, owner: str) -> list[TaskResponse]:
        return self._repository.list_by_owner(owner)

    def create_task(self, payload: TaskCreate, default_owner: str) -> TaskResponse:
        owner = default_owner if payload.owner is None else payload.owner
        return self._repository.insert(payload.title, payload.description, payload.status, owner, payload.priority)

    def summarize(self, owner: str) -> SummaryResponse:
        rows = self._repository.status_and_priority_by_owner(owner)
        return SummaryResponse(
            owner=owner,
            total=len(rows),
            by_status=dict(Counter(status for status, _ in rows)),
            high_priority_open=sum(1 for status, priority in rows if is_high_priority_open(status, priority)),
        )


class FileAlreadyExistsError(Exception):
    """Ya existe un archivo con ese nombre en el directorio de cargas (H-API-15)."""


class RequirementService:
    def __init__(self, upload_dir: str) -> None:
        self._upload_dir = Path(upload_dir)
        self._upload_dir.mkdir(parents=True, exist_ok=True)

    def store(self, filename: str | None, content: bytes) -> Path:
        target = self._upload_dir / str(filename)
        try:
            stored_file = target.open("xb")
        except FileExistsError as error:
            raise FileAlreadyExistsError(filename) from error
        try:
            with stored_file:
                stored_file.write(content)
        except OSError:
            target.unlink(missing_ok=True)
            raise
        return target


class BackendHealthService:
    def __init__(self, pool: urllib3.PoolManager) -> None:
        self._pool = pool

    def check(self) -> tuple[int, str]:
        try:
            response = self._pool.request("GET", auth_health_url(), timeout=HEALTH_TIMEOUT_SECONDS)
            return response.status, response.data.decode("utf-8")
        except (urllib3.exceptions.HTTPError, UnicodeDecodeError) as error:
            logger.warning("Auth backend health check failed: %s", error)
            return HEALTH_UNAVAILABLE_STATUS, HEALTH_UNAVAILABLE_MESSAGE
