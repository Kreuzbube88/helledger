from datetime import datetime
from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    category_type: str
    parent_id: int | None = None
    color: str | None = None
    icon: str | None = None


class CategoryUpdate(BaseModel):
    name: str | None = None
    category_type: str | None = None
    parent_id: int | None = None
    color: str | None = None
    icon: str | None = None
    default_account_id: int | None = None


class CategoryResponse(BaseModel):
    id: int
    household_id: int
    name: str
    category_type: str
    parent_id: int | None
    color: str | None
    icon: str | None
    archived: bool
    default_account_id: int | None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class CategoryTreeNode(BaseModel):
    id: int
    name: str
    category_type: str
    parent_id: int | None
    color: str | None
    icon: str | None
    archived: bool
    children: list["CategoryTreeNode"] = []
    model_config = {"from_attributes": True}


CategoryTreeNode.model_rebuild()
