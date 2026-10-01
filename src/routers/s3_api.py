# pyrefly: ignore [missing-import]
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from utils.s3_storage import storage
from utils.auth.dependencies import get_current_user, RoleChecker

s3_router = APIRouter(
    prefix="/api/s3_storage",
    tags=["S3 Storage"]
)

user_allowed = RoleChecker(["user"])


@s3_router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    _: bool = Depends(user_allowed)
    ):

    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Only images are allowed"
        )

    object_key = f"images/{file.filename}"

    storage.upload_file(
        file=file.file,
        object_key=object_key,
        content_type=file.content_type
    )

    url = storage.generate_url(
        object_key=object_key,
    )

    return {
        "filename": file.filename,
        "key": object_key,
        "url": url
    }