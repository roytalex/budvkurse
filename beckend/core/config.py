
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
