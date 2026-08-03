from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from core.deployment import Edition

_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

class UserBase(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr | None = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    slug: str = Field(..., min_length=2, max_length=100)
    edition: Edition = Edition.personal

    @field_validator("slug")
    @classmethod
    def slug_must_be_url_safe(cls, value: str) -> str:
        slug = value.strip().lower()
        if not _SLUG_PATTERN.fullmatch(slug):
            raise ValueError(
                "slug must be lowercase letters, digits, and single hyphens"
            )
        return slug

class UserLogin(BaseModel):
    slug: str = Field(..., min_length=2, max_length=100)
    username: str = Field(..., min_length=1, max_length=50)
    password: str

    @field_validator("slug")
    @classmethod
    def slug_must_be_url_safe(cls, value: str) -> str:
        slug = value.strip().lower()
        if not _SLUG_PATTERN.fullmatch(slug):
            raise ValueError(
                "slug must be lowercase letters, digits, and single hyphens"
            )
        return slug

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    role: str
    is_active: bool
    created_at: datetime

    @field_validator("id", "tenant_id", mode="before")
    @classmethod
    def coerce_uuid_fields(cls, value: object) -> str:
        return str(value)
