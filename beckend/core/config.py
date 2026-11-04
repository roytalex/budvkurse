
import re
from urllib.parse import urlsplit
from functools import lru_cache
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    database_url: str
    jwt_secret: str = Field(min_length=32)
    access_token_minutes: int = Field(default=15, ge=1, le=1440)
    refresh_token_days: int = Field(default=30, ge=1, le=365)
    cors_origins: list[str] = ["http://127.0.0.1:4174", "http://localhost:4174"]
    public_base_url: str = ""
    max_bot_token: str = ""
    max_bot_username: str = ""
    max_webhook_secret: str = ""
    max_ca_bundle: Path | None = None

    @field_validator("public_base_url")
    @classmethod
    def public_https(cls, value):
        if not value:
            return value
        parsed = urlsplit(value)
        if parsed.scheme != "https" or not parsed.hostname or "." not in parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/") or parsed.port not in (None, 443):
            raise ValueError("Публичный URL должен быть HTTPS-адресом сайта без пути и параметров")
        return value.rstrip("/")

    @field_validator("max_bot_username")
    @classmethod
    def bot_name(cls, value):
        if value and not re.fullmatch(r"[A-Za-z0-9_]{1,64}", value):
            raise ValueError("MAX_BOT_USERNAME: имя без @ и ссылки")
        return value

    @field_validator("max_bot_token")
    @classmethod
    def bot_token(cls, value):
        if any(c.isspace() for c in value):
            raise ValueError("MAX_BOT_TOKEN не должен содержать пробелы или переносы строк")
        return value

    @field_validator("max_webhook_secret")
    @classmethod
    def webhook_secret(cls, value):
        if value and not re.fullmatch(r"[A-Za-z0-9_-]{32,256}", value):
            raise ValueError("MAX_WEBHOOK_SECRET: от 32 до 256 латинских букв, цифр, _ или -")
        return value

    @field_validator("max_ca_bundle", mode="before")
    @classmethod
    def optional_ca(cls, value):
        return value or None

    geocoder_url: str = "https://photon.komoot.io/api/"
    upload_dir: Path = ROOT / "uploads"
    max_upload_bytes: int = Field(default=5 * 1024 * 1024, ge=1024, le=20 * 1024 * 1024)

    @field_validator("database_url")
    @classmethod
    def database_driver(cls, value: str) -> str:
        if not value.startswith(("postgresql+asyncpg://", "sqlite+aiosqlite://")):
            raise ValueError("Используй URL postgresql+asyncpg://")
        return value

    @field_validator("jwt_secret")
    @classmethod
    def real_secret(cls, value: str) -> str:
        if value.startswith("REPLACE_"):
            raise ValueError("Сгенерируй JWT_SECRET и запиши его в .env")
        return value

    @field_validator("upload_dir")
    @classmethod
    def absolute_upload_path(cls, value: Path) -> Path:
        return value if value.is_absolute() else ROOT / value


@lru_cache
def get_settings() -> Settings:
    return Settings()
