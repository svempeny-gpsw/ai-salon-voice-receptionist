from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://salon_user:salon_password@localhost:5432/salon"
    salon_config_path: str = "config/salon.example.json"
    n8n_webhook_url: str = "http://localhost:5678/webhook/salon-booking"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
