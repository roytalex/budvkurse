import hmac
import json
from fastapi import APIRouter, Request, Response
from pydantic import Field
from schemas.common import InputModel
from api.deps import DB, CurrentUser
from services import max_notifications
from core.config import get_settings
from core.errors import AppError
from services import max_bot

router = APIRouter(prefix='/integrations/max', tags=['MAX'])


@router.post('/webhook', summary='События MAX, защищённые секретом webhook')
async def webhook(request: Request):
    settings = get_settings()
    if not settings.max_bot_token or not settings.max_webhook_secret or not settings.max_bot_username:
        raise AppError(503, 'Бот MAX ещё не настроен')
    supplied = request.headers.get('X-Max-Bot-Api-Secret', '')
    if not hmac.compare_digest(supplied.encode(), settings.max_webhook_secret.encode()):
        raise AppError(403, 'Неверный секрет webhook')
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > 65536:
            raise AppError(413, 'Слишком большой запрос')
    try:
        update = json.loads(raw)
        if not isinstance(update, dict):
            raise ValueError()
        for field in ('user', 'message'):
            if field in update and not isinstance(update[field], dict):
                raise ValueError()
        if 'message' in update:
            for field in ('body', 'sender', 'recipient'):
                if field in update['message'] and not isinstance(update['message'][field], dict):
                    raise ValueError()
            if not isinstance((update['message'].get('body') or {}).get('text', ''), (str, type(None))):
                raise ValueError()
    except (ValueError, UnicodeDecodeError):
        raise AppError(422, 'Некорректное событие MAX') from None
    await max_bot.process(update)
    return {'ok': True}


class MaxConnectRequest(InputModel):
    init_data: str = Field(min_length=1, max_length=16000)


@router.get('/connection', summary='Статус подключения напоминаний MAX')
async def connection(db: DB, user: CurrentUser):
    return await max_notifications.status(db, user)


@router.post('/connection', summary='Подключить MAX по подписанным данным мини-приложения')
async def connect(data: MaxConnectRequest, db: DB, user: CurrentUser):
    return await max_notifications.connect(db, user, data.init_data)


@router.delete('/connection', status_code=204, summary='Отключить напоминания MAX')
async def disconnect(db: DB, user: CurrentUser):
    await max_notifications.disconnect(db, user)
    return Response(status_code=204)
