from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    SECRET_KEY: str
    DATABASE_PATH: str = "/data/helledger.db"
    BACKUP_PATH: str = "/backups"
    BACKUP_INTERVAL_HOURS: int = 24
    PORT: int = 3000
    TZ: str = "Europe/Berlin"
    DEFAULT_LANGUAGE: str = "de"
    DEFAULT_CURRENCY: str = "EUR"
    ALLOW_REGISTRATION: bool = True
    FIRST_USER_IS_ADMIN: bool = True
    LOG_LEVEL: str = "INFO"
    TRUST_PROXY_HEADER: bool = True
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    TESTING: bool = False

    # OIDC (optional)
    OIDC_ENABLED: bool = False
    OIDC_CLIENT_ID: str = ""
    OIDC_CLIENT_SECRET: str = ""
    OIDC_DISCOVERY_URL: str = ""  # e.g. https://accounts.google.com/.well-known/openid-configuration

    # SMTP (optional)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""   # defaults to SMTP_USER if empty
    SMTP_TLS: bool = True


settings = Settings()
