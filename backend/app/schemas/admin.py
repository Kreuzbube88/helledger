from pydantic import BaseModel


class AdminStatus(BaseModel):
    user_count: int
    household_count: int
    transaction_count: int
    db_size_bytes: int
    allow_registration: bool


class AdminSettings(BaseModel):
    allow_registration: bool
    default_language: str
    oidc_enabled: bool
    oidc_client_id: str
    oidc_discovery_url: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_from: str


class AdminSettingsPatch(BaseModel):
    allow_registration: bool | None = None
    default_language: str | None = None
    oidc_enabled: bool | None = None
    oidc_client_id: str | None = None
    oidc_client_secret: str | None = None
    oidc_discovery_url: str | None = None
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
