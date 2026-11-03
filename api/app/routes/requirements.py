from fastapi import APIRouter, Depends, File, UploadFile

from app.dependencies import get_requirement_service
from app.schemas import UploadResponse
from app.security import Identity, legacy_identity
from app.services import RequirementService

router = APIRouter(prefix="/api")


@router.post("/requirements", status_code=201, response_model=UploadResponse)
async def upload_requirement(
    file: UploadFile = File(...),
    identity: Identity = Depends(legacy_identity),
    service: RequirementService = Depends(get_requirement_service),
) -> UploadResponse:
    content = await file.read()
    stored_at = service.store(file.filename, content)
    return UploadResponse(owner=identity["username"], file_name=file.filename, stored_at=str(stored_at), size=len(content))
