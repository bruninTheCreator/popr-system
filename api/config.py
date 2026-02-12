from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os


def _get_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None:
        return default
    return value


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


@dataclass(frozen=True)
class Settings:
    database_url: str
    sap_system_id: str
    sap_client: str
    sap_user: str
    sap_password: str
    sap_language: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_from_email: str
    smtp_from_name: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        database_url=_get_env("DATABASE_URL", "sqlite+aiosqlite:///./popr.db"),
        sap_system_id=_get_env("SAP_SYSTEM_ID", "PRD"),
        sap_client=_get_env("SAP_CLIENT", "100"),
        sap_user=_get_env("SAP_USER", "SAP_USER"),
        sap_password=_get_env("SAP_PASSWORD", "SAP_PASS"),
        sap_language=_get_env("SAP_LANGUAGE", "PT"),
        smtp_host=_get_env("SMTP_HOST", "smtp.gmail.com"),
        smtp_port=_get_int("SMTP_PORT", 587),
        smtp_user=_get_env("SMTP_USER", "popr@company.com"),
        smtp_password=_get_env("SMTP_PASSWORD", "app_password"),
        smtp_from_email=_get_env("SMTP_FROM_EMAIL", "popr@company.com"),
        smtp_from_name=_get_env("SMTP_FROM_NAME", "POPR System"),
    )
