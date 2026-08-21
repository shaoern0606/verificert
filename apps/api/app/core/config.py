from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "VERIFICERT"
    database_url: str = "sqlite:///./verificert_demo.db"
    jwt_secret: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    jwt_minutes: int = 60
    openai_api_key: str | None = None
    blockchain_rpc_url: str = "http://127.0.0.1:8545"
    blockchain_private_key: str | None = None
    verificert_contract_address: str | None = None
    next_public_app_url: str = "http://localhost:3000"
    storage_path: Path = Path("./storage")
    demo_mode: bool = True
    max_upload_mb: int = 10

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    return settings
