import hashlib
from dataclasses import dataclass
from datetime import datetime

from app.core.config import get_settings


@dataclass
class ChainReceipt:
    transaction_hash: str
    block_number: int
    contract_address: str
    network: str = "hardhat-local"


class BlockchainService:
    """Single boundary for chain operations. Demo mode returns deterministic local receipts."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def _receipt(self, action: str, certificate_id: str) -> ChainReceipt:
        seed = f"{action}:{certificate_id}:{self.settings.verificert_contract_address or 'demo'}"
        tx = "0x" + hashlib.sha256(seed.encode()).hexdigest()
        block = int(hashlib.sha256((seed + "block").encode()).hexdigest()[:6], 16)
        return ChainReceipt(
            transaction_hash=tx,
            block_number=block,
            contract_address=self.settings.verificert_contract_address or "0x0000000000000000000000000000000000000000",
        )

    def issue_certificate(self, certificate_id: str, document_hash: str, expires_at: datetime | None, metadata_uri: str) -> ChainReceipt:
        return self._receipt("issue", certificate_id + document_hash + metadata_uri)

    def verify_certificate(self, certificate_id: str) -> dict:
        return {"certificate_id": certificate_id, "record_found": True, "network": "hardhat-local"}

    def revoke_certificate(self, certificate_id: str) -> ChainReceipt:
        return self._receipt("revoke", certificate_id)

    def register_issuer(self, issuer: str) -> ChainReceipt:
        return self._receipt("register_issuer", issuer)

    def suspend_issuer(self, issuer: str) -> ChainReceipt:
        return self._receipt("suspend_issuer", issuer)

    def get_certificate(self, certificate_id: str) -> dict:
        return self.verify_certificate(certificate_id)
