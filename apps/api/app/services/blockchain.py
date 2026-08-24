from dataclasses import dataclass
from datetime import datetime
from typing import Any

from eth_account import Account
from web3 import Web3

from app.core.config import get_settings


CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "certificateId", "type": "string"},
            {"internalType": "bytes32", "name": "documentHash", "type": "bytes32"},
            {"internalType": "uint256", "name": "expiresAt", "type": "uint256"},
            {"internalType": "string", "name": "metadataURI", "type": "string"},
        ],
        "name": "issueCertificate",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "string", "name": "certificateId", "type": "string"}],
        "name": "verifyCertificate",
        "outputs": [
            {"internalType": "bool", "name": "exists", "type": "bool"},
            {"internalType": "bytes32", "name": "documentHash", "type": "bytes32"},
            {"internalType": "address", "name": "issuer", "type": "address"},
            {"internalType": "bool", "name": "revoked", "type": "bool"},
            {"internalType": "uint256", "name": "expiresAt", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "string", "name": "certificateId", "type": "string"}],
        "name": "revokeCertificate",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "issuer", "type": "address"}],
        "name": "registerIssuer",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "issuer", "type": "address"}],
        "name": "suspendIssuer",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "issuer", "type": "address"}],
        "name": "isApprovedIssuer",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "string", "name": "certificateId", "type": "string"}],
        "name": "getCertificate",
        "outputs": [
            {
                "components": [
                    {"internalType": "bytes32", "name": "documentHash", "type": "bytes32"},
                    {"internalType": "address", "name": "issuer", "type": "address"},
                    {"internalType": "uint256", "name": "issuedAt", "type": "uint256"},
                    {"internalType": "uint256", "name": "expiresAt", "type": "uint256"},
                    {"internalType": "bool", "name": "revoked", "type": "bool"},
                    {"internalType": "string", "name": "metadataURI", "type": "string"},
                ],
                "internalType": "struct VerifiCertRegistry.Certificate",
                "name": "",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
]


@dataclass
class ChainReceipt:
    transaction_hash: str
    block_number: int
    contract_address: str
    network: str


class BlockchainService:
    """Single boundary for blockchain contract interaction via Web3 RPC."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.rpc_url = self.settings.blockchain_rpc_url
        self.contract_address = self.settings.verificert_contract_address
        if not self.contract_address:
            raise ValueError("VERIFICERT_CONTRACT_ADDRESS is not configured.")

        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError(f"Could not connect to blockchain RPC: {self.rpc_url}")

        self.contract_address = Web3.to_checksum_address(self.contract_address)
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=CONTRACT_ABI)

    @property
    def network_name(self) -> str:
        return self.settings.blockchain_network_name

    @staticmethod
    def _normalize_bytes32(value: str) -> str:
        if value is None:
            raise ValueError("document_hash is required")
        value = value.strip()
        if value.startswith("0x") or value.startswith("0X"):
            normalized = value
        else:
            normalized = f"0x{value}"
        if len(normalized) != 66:
            raise ValueError(f"document_hash must be a 32-byte hex string, got {value!r}")
        return normalized

    def _require_private_key(self) -> str:
        private_key = self.settings.blockchain_private_key
        if not private_key:
            raise ValueError("blockchain_private_key is not configured for state-changing transactions.")
        return private_key

    def _account(self, private_key: str | None = None) -> Account:
        return Account.from_key(private_key or self._require_private_key())

    def signer_address(self) -> str:
        return self._account().address

    def admin_signer(self) -> Account:
        return self._account(self.settings.blockchain_admin_private_key)

    def get_signer_for_issuer(self, wallet_address: str) -> Account:
        target = Web3.to_checksum_address(wallet_address).lower()
        configured = (
            (self.settings.abc_academy_wallet_address, self.settings.abc_academy_private_key),
            (self.settings.northbridge_wallet_address, self.settings.northbridge_private_key),
            (self.settings.cloudskills_wallet_address, self.settings.cloudskills_private_key),
            (self.settings.brightpath_wallet_address, self.settings.brightpath_private_key),
            (self.settings.techbridge_wallet_address, self.settings.techbridge_private_key),
        )
        for configured_wallet, private_key in configured:
            if configured_wallet and configured_wallet.lower() == target:
                if not private_key:
                    raise ValueError(f"No private key is configured for issuer wallet {wallet_address}.")
                signer = self._account(private_key)
                if signer.address.lower() != target:
                    raise ValueError(f"Configured private key does not match issuer wallet {wallet_address}.")
                return signer
            if private_key and not configured_wallet:
                signer = self._account(private_key)
                if signer.address.lower() == target:
                    return signer
        if self.settings.blockchain_private_key:
            signer = self._account()
            if signer.address.lower() == target:
                return signer
        raise ValueError(f"No blockchain signer is configured for issuer wallet {wallet_address}.")

    def _build_tx(self, transaction_call: Any, private_key: str | None = None, signer: Account | None = None):
        signer = signer or self._account(private_key)
        tx = transaction_call.build_transaction(
            {
                "from": signer.address,
                "nonce": self.w3.eth.get_transaction_count(signer.address),
                "gas": self.settings.blockchain_gas_limit,
                "chainId": self.w3.eth.chain_id,
            }
        )
        return signer, tx

    def _send_transaction(self, transaction_call: Any, private_key: str | None = None, signer: Account | None = None) -> ChainReceipt:
        signer, tx = self._build_tx(transaction_call, private_key, signer)
        signed_tx = signer.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=self.settings.blockchain_tx_timeout_seconds)
        if receipt.get("status") != 1:
            raise RuntimeError(f"Blockchain transaction reverted: {Web3.to_hex(tx_hash)}")
        return ChainReceipt(
            transaction_hash=Web3.to_hex(tx_hash),
            block_number=receipt["blockNumber"],
            contract_address=self.contract_address,
            network=self.network_name,
        )

    def issue_certificate(self, certificate_id: str, document_hash: str, expires_at: datetime | None, metadata_uri: str, signer: Account | None = None) -> ChainReceipt:
        expires_ts = int(expires_at.timestamp()) if expires_at else 0
        tx_call = self.contract.functions.issueCertificate(
            certificate_id,
            self._normalize_bytes32(document_hash),
            expires_ts,
            metadata_uri,
        )
        return self._send_transaction(tx_call, signer=signer)

    def verify_certificate(self, certificate_id: str) -> dict:
        result = self.contract.functions.verifyCertificate(certificate_id).call()
        exists, document_hash, issuer, revoked, expires_at = result
        return {
            "certificate_id": certificate_id,
            "record_found": bool(exists),
            "document_hash": Web3.to_hex(document_hash) if exists else None,
            "issuer": issuer,
            "revoked": bool(revoked),
            "expires_at": expires_at,
            "network": self.network_name,
            "contract_address": self.contract_address,
        }

    def revoke_certificate(self, certificate_id: str, signer: Account | None = None) -> ChainReceipt:
        tx_call = self.contract.functions.revokeCertificate(certificate_id)
        return self._send_transaction(tx_call, signer=signer)

    def register_issuer(self, issuer: str) -> ChainReceipt:
        tx_call = self.contract.functions.registerIssuer(Web3.to_checksum_address(issuer))
        return self._send_transaction(tx_call, self.settings.blockchain_admin_private_key)

    def suspend_issuer(self, issuer: str) -> ChainReceipt:
        tx_call = self.contract.functions.suspendIssuer(Web3.to_checksum_address(issuer))
        return self._send_transaction(tx_call, self.settings.blockchain_admin_private_key)

    def is_approved_issuer(self, issuer: str) -> bool:
        return bool(self.contract.functions.isApprovedIssuer(Web3.to_checksum_address(issuer)).call())

    def get_certificate(self, certificate_id: str) -> dict:
        certificate = self.contract.functions.getCertificate(certificate_id).call()
        document_hash, issuer, issued_at, expires_at, revoked, metadata_uri = certificate
        return {
            "certificate_id": certificate_id,
            "document_hash": Web3.to_hex(document_hash),
            "issuer": issuer,
            "issued_at": issued_at,
            "expires_at": expires_at,
            "revoked": bool(revoked),
            "metadata_uri": metadata_uri,
        }
