from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.dependencies import get_requirement_service
from app.schemas import UploadResponse
from app.security import Identity, legacy_identity
from app.services import FileAlreadyExistsError, RequirementService

CONFLICT = 409
FILE_EXISTS_DETAIL = "File already exists"

router = APIRouter(prefix="/api")


@router.post(
    "/requirements",
    status_code=201,
    response_model=UploadResponse,
    responses={CONFLICT: {"description": FILE_EXISTS_DETAIL}},
)
async def upload_requirement(
    file: UploadFile = File(...),
    identity: Identity = Depends(legacy_identity),
    service: RequirementService = Depends(get_requirement_service),
) -> UploadResponse:
    content = await file.read()
    try:
        stored_at = service.store(file.filename, content)
    except FileAlreadyExistsError as error:
        raise HTTPException(status_code=CONFLICT, detail=FILE_EXISTS_DETAIL) from error
    return UploadResponse(owner=identity["username"], file_name=file.filename, stored_at=str(stored_at), size=len(content))
