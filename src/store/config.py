"""Application configuration.

Settings load once from environment (prefixed ``STORE_``) or a ``.env`` file.
Keeping config in a typed object — not scattered ``os.getenv`` calls — means a
missing or malformed value fails loudly at startup, not deep in a request.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="STORE_", env_file=".env")

    database_url: str = "sqlite:///store.db"


settings = Settings()
