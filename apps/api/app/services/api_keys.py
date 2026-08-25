import hashlib
import secrets

KEY_PREFIX = "vcert_live_"


def generate_api_key() -> tuple[str, str, str]:
    token = secrets.token_urlsafe(32)
    raw_key = f"{KEY_PREFIX}{token}"
    return raw_key, hash_api_key(raw_key), raw_key[: len(KEY_PREFIX) + 6]


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
