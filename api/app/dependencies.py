from fastapi import Request

from app.services import BackendHealthService, RequirementService, TaskService


def get_task_service(request: Request) -> TaskService:
    return request.app.state.task_service


def get_requirement_service(request: Request) -> RequirementService:
    return request.app.state.requirement_service


def get_health_service(request: Request) -> BackendHealthService:
    return request.app.state.health_service
