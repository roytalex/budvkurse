
import hashlib
import secrets
from datetime import timedelta
import jwt
from pwdlib import PasswordHash
from core.config import get_settings
from core.time import utcnow

password_hasher = PasswordHash.recommended()

DUMMY_HASH = password_hasher.hash(secrets.token_urlsafe(24))


def hash_refresh(token):
    return hashlib.sha256(token.encode()).hexdigest()


def access_token(user_id, session_id):
    settings = get_settings()
    now = utcnow()
    return jwt.encode({"sub": str(user_id), "sid": session_id, "iat": now,
                       "exp": now + timedelta(minutes=settings.access_token_minutes),
                       "type": "access"}, settings.jwt_secret, algorithm="HS256")


def decode_access(token):
    claims = jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"],
                        options={"require": ["sub", "sid", "iat", "exp", "type"]})
    if claims["type"] != "access" or not isinstance(claims["sid"], int):
        raise jwt.InvalidTokenError("Wrong token type")
    int(claims["sub"])
    return claims
