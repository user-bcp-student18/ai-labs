from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.config import (
    DEFAULT_PRIORITY,
    DEFAULT_STATUS,
    DESCRIPTION_MAX_LENGTH,
    TITLE_MAX_LENGTH,
    TaskPriority,
    TaskStatus,
)


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=TITLE_MAX_LENGTH)
    description: str = Field(default="", max_length=DESCRIPTION_MAX_LENGTH)
    status: TaskStatus = DEFAULT_STATUS
    priority: TaskPriority = DEFAULT_PRIORITY
    owner: str | None = None


class TaskResponse(CamelModel):
    id: int
    title: str
    description: str
    status: str
    owner: str
    priority: str
    created_at: str


class SummaryResponse(CamelModel):
    owner: str
    total: int
    by_status: dict[str, int]
    high_priority_open: int


class UploadResponse(CamelModel):
    owner: str
    file_name: str | None
    stored_at: str
    size: int


class BackendHealthResponse(CamelModel):
    requested_by: str
    status: int
    body: str
