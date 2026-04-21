from pydantic import BaseModel, Field


class BackupItem(BaseModel):
    filename: str
    size_bytes: int
    created_at: str


class BackupSettings(BaseModel):
    backup_retention_days: int


class BackupSettingsPatch(BaseModel):
    backup_retention_days: int = Field(..., ge=1)
