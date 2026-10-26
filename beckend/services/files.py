
import io
import secrets
import warnings
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from sqlalchemy import exists, select
from starlette.concurrency import run_in_threadpool
from core.config import get_settings
from core.errors import AppError
from crud import files
from db.models import Event, File
from .common import require_row


def inspect_image(content):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as img:
                if img.format not in ("JPEG", "PNG", "WEBP"):
                    raise AppError(422, "Разрешены JPEG, PNG и WEBP")
                if img.width * img.height > 25_000_000:
                    raise AppError(422, "Изображение слишком большое: максимум 25 мегапикселей")
                fmt = img.format
                img.verify()
        return {"JPEG": ("jpg", "image/jpeg"), "PNG": ("png", "image/png"), "WEBP": ("webp", "image/webp")}[fmt]
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise AppError(422, "Файл не является корректным изображением")


def file_read(row):
    return {"id": row.id, "url": f"/api/v1/files/{row.id}/content", "mime_type": row.mime_type, "size_bytes": row.size_bytes}


async def upload(db, user, upload_file):
    settings = get_settings()
    content = await upload_file.read(settings.max_upload_bytes + 1)
    await upload_file.close()
    if len(content) > settings.max_upload_bytes:
        raise AppError(413, "Файл больше разрешённого размера")
    extension, mime = await run_in_threadpool(inspect_image, content)
    key = f"{secrets.token_hex(20)}.{extension}"
    directory = settings.upload_dir
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / key
    await run_in_threadpool(path.write_bytes, content)

    db.info.setdefault("rollback_files", []).append(path)
    row = await files.create_file(db, {"uploaded_by": user.id, "storage_key": key,
        "original_name": (upload_file.filename or "image").replace("\\", "/").split("/")[-1][:255],
        "mime_type": mime, "size_bytes": len(content)})
    return file_read(row)


async def get_content(db, file_id, user):
    row = await require_row(db, File, file_id)
    owner = user and (row.uploaded_by == user.id or user.role == "admin")
    public = await db.scalar(select(exists().where(Event.cover_file_id == row.id, Event.status.in_(["published", "cancelled"]))))
    if not owner and not public:
        raise AppError(404, "Файл не найден")
    path = get_settings().upload_dir / row.storage_key
    if not path.is_file():
        raise AppError(404, "Файл отсутствует в хранилище")
    return row, path


async def remove(db, user, file_id):
    row = await require_row(db, File, file_id, lock=True)
    if row.uploaded_by != user.id and user.role != "admin":
        raise AppError(403, "Это чужой файл")
    if await db.scalar(select(exists().where(Event.cover_file_id == file_id))):
        raise AppError(409, "Файл используется как обложка мероприятия")
    path = get_settings().upload_dir / row.storage_key
    await files.delete_file(db, row)

    db.info.setdefault("commit_delete_files", []).append(path)
