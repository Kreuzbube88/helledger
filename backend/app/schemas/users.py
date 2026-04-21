from datetime import datetime
from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str
    language: str
    is_active: bool
    created_at: datetime
    last_login: datetime | None

    model_config = {"from_attributes": True}


class UserPatch(BaseModel):
    name: str | None = None
    role: str | None = None
    is_active: bool | None = None
    language: str | None = None


class PreferencesOut(BaseModel):
    language: str
    model_config = {"from_attributes": True}


class PreferencesPatch(BaseModel):
    language: str | None = None


class ProfilePatch(BaseModel):
    name: str | None = None
    language: str | None = None
