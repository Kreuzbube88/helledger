from datetime import datetime
from pydantic import BaseModel


class HouseholdCreate(BaseModel):
    name: str


class HouseholdUpdate(BaseModel):
    name: str | None = None


class HouseholdResponse(BaseModel):
    id: int
    name: str
    owner_id: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class MemberCreate(BaseModel):
    email: str


class MemberUpdate(BaseModel):
    role: str


class MemberDetailResponse(BaseModel):
    user_id: int
    name: str
    email: str
    role: str
    created_at: datetime
    model_config = {"from_attributes": True}
