from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Query, Response
from fastapi.responses import HTMLResponse
import jwt
from api.deps import DB, CurrentUser
from core.config import get_settings
from core.errors import AppError
from core.time import utcnow
from db.models import User
from services import activity

router = APIRouter(tags=['Экспорт для мини-приложения'])


@router.post('/events/{event_id}/certificate-link', summary='Ссылка на собственный сертификат на 5 минут')
async def issue_certificate_link(event_id: int, db: DB, user: CurrentUser, response: Response):
    await activity.certificate(db, user, event_id)
    now = utcnow()
    token = jwt.encode({'sub': str(user.id), 'event_id': event_id, 'type': 'certificate-download',
                        'iat': now, 'exp': now + timedelta(minutes=5)}, get_settings().jwt_secret, algorithm='HS256')
    response.headers['Cache-Control'] = 'no-store'
    return {'path': '/api/v1/exports/certificate?token=' + token,
            'filename': f'certificate-{event_id}-{user.id}.html'}


@router.get('/exports/certificate', response_class=HTMLResponse, summary='Скачать сертификат по короткоживущей подписанной ссылке')
async def download_certificate(db: DB, token: Annotated[str, Query(min_length=20, max_length=2000)]):
    try:
        claims = jwt.decode(token, get_settings().jwt_secret, algorithms=['HS256'],
                            options={'require': ['sub', 'event_id', 'type', 'iat', 'exp']})
        if claims['type'] != 'certificate-download' or type(claims['event_id']) is not int:
            raise ValueError()
        user_id = int(claims['sub'])
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise AppError(401, 'Ссылка недействительна или истекла. Создай новую в паспорте.') from None
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise AppError(401, 'Аккаунт неактивен')
    content = await activity.certificate(db, user, claims['event_id'])
    return HTMLResponse(content, headers={'Content-Disposition': f'attachment; filename="certificate-{claims["event_id"]}-{user_id}.html"',
                                         'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer', 'X-Content-Type-Options': 'nosniff'})
