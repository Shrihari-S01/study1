"""Upload endpoints."""

from fastapi import APIRouter, File, UploadFile, status

from app.api.deps import DbSession
from app.schemas.response import ApiResponse
from app.schemas.upload import UploadCreateResponse, UploadRead
from app.services.storage.upload_service import UploadService 


router = APIRouter()


# @router.post("", response_model=ApiResponse[UploadCreateResponse], status_code=status.HTTP_201_CREATED)
# async def upload_notice(db: DbSession, file: UploadFile = File(...)) -> ApiResponse[UploadCreateResponse]:
#     """Upload a newspaper auction notice image or PDF."""
#     upload = await UploadService(db).create_upload(file)
#     payload = UploadCreateResponse(
#         upload=UploadRead.model_validate(upload),
#         process_url=f"/api/v1/process/{upload.id}",
#     )
#     return ApiResponse(message="File uploaded successfully", data=payload)

@router.post("", response_model=ApiResponse[UploadCreateResponse], status_code=status.HTTP_201_CREATED)
async def upload_notice(db: DbSession, file: UploadFile = File(...)):
    print("========== API START ==========")

    upload = await UploadService(db).create_upload(file)

    print("========== API END ==========")

    payload = UploadCreateResponse(
        upload=UploadRead.model_validate(upload),
        process_url=f"/api/v1/process/{upload.id}",
    )

    return ApiResponse(
        message="File uploaded successfully",
        data=payload,
    )


