from fastapi import APIRouter, Response, UploadFile
from fastapi.responses import FileResponse
from api.deps import DB, OptionalUser, Organizer
from schemas.files import FileRead
from services import files

router = APIRouter(prefix="/files", tags=["Фотографии"])


@router.post("", response_model=FileRead, status_code=201, summary="Загрузить фотографию")
async def upload(file: UploadFile, db: DB, user: Organizer):
    return await files.upload(db, user, file)


@router.get("/{file_id}/content", summary="Изображение; чужие неопубликованные обложки скрыты")
async def content(file_id: int, db: DB, user: OptionalUser):
    row, path = await files.get_content(db, file_id, user)
    return FileResponse(path, media_type=row.mime_type, headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-cache"})


@router.delete("/{file_id}", status_code=204, summary="Удалить неиспользуемую фотографию")
async def delete(file_id: int, db: DB, user: Organizer):
    await files.remove(db, user, file_id)
    return Response(status_code=204)
