from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    app_name: str = "VERIFICERT"
    database_url: str = "postgresql+psycopg://verificert:verificert@localhost:5432/verificert"
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_minutes: int = 60
    openai_api_key: str | None = None
    blockchain_rpc_url: str = "http://127.0.0.1:8545"
    blockchain_private_key: str | None = None
    blockchain_admin_private_key: str | None = None
    abc_academy_private_key: str | None = None
    northbridge_private_key: str | None = None
    cloudskills_private_key: str | None = None
    brightpath_private_key: str | None = None
    techbridge_private_key: str | None = None
    abc_academy_wallet_address: str | None = None
    northbridge_wallet_address: str | None = None
    cloudskills_wallet_address: str | None = None
    brightpath_wallet_address: str | None = None
    techbridge_wallet_address: str | None = None
    verificert_contract_address: str | None = None
    blockchain_network_name: str = "hardhat-local"
    blockchain_explorer_tx_url: str | None = None
    blockchain_tx_timeout_seconds: int = 120
    blockchain_gas_limit: int = 750000
    require_blockchain: bool = True
    next_public_app_url: str = "http://localhost:3000"
    storage_path: Path = Path("./storage")
    max_upload_mb: int = 10

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    return settings