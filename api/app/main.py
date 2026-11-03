from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import urllib3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.repository import TaskRepository
from app.routes import health, requirements, tasks
from app.services import BackendHealthService, RequirementService, TaskService


def create_app(db_path: str | None = None, upload_dir: str | None = None) -> FastAPI:
    selected_uploads = upload_dir or config.upload_dir()
    repository = TaskRepository(db_path or config.db_path())
    repository.init_schema()
    repository.seed_if_empty()
    http_pool = urllib3.PoolManager()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        repository.close()
        http_pool.clear()

    app = FastAPI(title="Workshop Requirements API", version="0.1.0", lifespan=lifespan)
    app.state.connection = repository.connection
    app.state.upload_dir = selected_uploads
    app.state.task_service = TaskService(repository)
    app.state.requirement_service = RequirementService(selected_uploads)
    app.state.health_service = BackendHealthService(http_pool)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins(),
        allow_credentials=True,
        allow_methods=list(config.CORS_ALLOWED_METHODS),
        allow_headers=list(config.CORS_ALLOWED_HEADERS),
    )
    for router_module in (tasks, requirements, health):
        app.include_router(router_module.router)

    return app


app = create_app()
