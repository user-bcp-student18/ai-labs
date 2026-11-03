from fastapi import APIRouter, Body, Depends, Query

from app.dependencies import get_task_service
from app.schemas import SummaryResponse, TaskCreate, TaskResponse
from app.security import Identity, legacy_identity
from app.services import TaskService, resolve_owner

router = APIRouter(prefix="/api")


@router.get("/tasks", response_model=list[TaskResponse])
def list_tasks(
    owner: str | None = Query(default=None),
    identity: Identity = Depends(legacy_identity),
    service: TaskService = Depends(get_task_service),
) -> list[TaskResponse]:
    return service.list_tasks(resolve_owner(owner, identity))


@router.post("/tasks", status_code=201, response_model=TaskResponse)
def create_task(
    payload: TaskCreate = Body(...),
    identity: Identity = Depends(legacy_identity),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    return service.create_task(payload, identity["username"])


@router.get("/summary", response_model=SummaryResponse)
def summary(
    owner: str | None = Query(default=None),
    identity: Identity = Depends(legacy_identity),
    service: TaskService = Depends(get_task_service),
) -> SummaryResponse:
    return service.summarize(resolve_owner(owner, identity))
