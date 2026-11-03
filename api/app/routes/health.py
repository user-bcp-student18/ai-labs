from fastapi import APIRouter, Depends

from app.dependencies import get_health_service
from app.schemas import BackendHealthResponse
from app.security import Identity, legacy_identity
from app.services import BackendHealthService

router = APIRouter(prefix="/api")


@router.get("/backend-health", response_model=BackendHealthResponse)
def backend_health(
    identity: Identity = Depends(legacy_identity),
    service: BackendHealthService = Depends(get_health_service),
) -> BackendHealthResponse:
    status, body = service.check()
    return BackendHealthResponse(requested_by=identity["username"], status=status, body=body)
