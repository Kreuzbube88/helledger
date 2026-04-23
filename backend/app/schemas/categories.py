from datetime import datetime
from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    category_type: str
    parent_id: int | None = None
    color: str | None = None
    icon: str | None = None
    is_savings: bool = False


class CategoryUpdate(BaseModel):
    name: str | None = None
    category_type: str | None = None
    parent_id: int | None = None
    color: str | None = None
    icon: str | None = None
    is_savings: bool = False


class CategoryResponse(BaseModel):
    id: int
    household_id: int
    name: str
    category_type: str
    parent_id: int | None
    color: str | None
    icon: str | None
    is_savings: bool
    archived: bool
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
