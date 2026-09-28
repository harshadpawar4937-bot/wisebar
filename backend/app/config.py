from __future__ import annotations

import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


def _on_vercel() -> bool:
    return any(os.environ.get(key) for key in ("VERCEL", "VERCEL_ENV", "VERCEL_URL"))


def _database_url() -> str:
    # Vercel’s app filesystem is read-only. /tmp is the writable location.
    if _on_vercel():
        return "sqlite:////tmp/wisebar.db"
    return "sqlite:///./wisebar.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = _database_url()
    secret_key: str = "dev-only-change-me"
    debug: bool = True
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    admin_email: str = "admin@wisebar.example"
    admin_password: str = "change-me-now"
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""
    ga_measurement_id: str = ""
    s3_endpoint: str = ""
    s3_bucket: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_public_base: str = ""
    smtp_host: str = ""
    smtp_from: str = ""
    access_token_minutes: int = 60 * 24 * 14

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def payments_configured(self) -> bool:
        return bool(self.razorpay_key_id and self.razorpay_key_secret)

    @property
    def storage_configured(self) -> bool:
        return bool(self.s3_endpoint and self.s3_bucket and self.s3_access_key and self.s3_secret_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
