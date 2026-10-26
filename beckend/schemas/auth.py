from typing import Literal
from pydantic import EmailStr, Field, SecretStr, field_validator
from .common import InputModel, ReadModel


class RegisterRequest(InputModel):
    email: EmailStr
    password: SecretStr = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=80)
    role: Literal["student", "organizer"] = "student"

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return str(value).lower()


class LoginRequest(InputModel):
    email: EmailStr
    password: SecretStr = Field(min_length=1, max_length=128)


class RefreshRequest(InputModel):
    refresh_token: str = Field(min_length=32, max_length=512)


class TokenPair(ReadModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
