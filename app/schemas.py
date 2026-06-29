from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApiKeyResponse(BaseModel):
    id: int
    prefix: str
    api_key: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShortLinkCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: Optional[str] = Field(default=None, min_length=3, max_length=20)
    expires_at: Optional[datetime] = None
    password: Optional[str] = Field(default=None, min_length=4)
    redirect_type: Literal[301, 302] = 302


class ShortLinkResponse(BaseModel):
    id: int
    original_url: str
    short_code: str
    short_url: str
    expires_at: Optional[datetime] = None
    redirect_type: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)