from types import SimpleNamespace

from eth_account import Account


def test_issue_certificate_uses_web3_contract(monkeypatch):
    seen = {}

    class FakeContractFunction:
        def __init__(self, method_name):
            self.method_name = method_name

        def build_transaction(self, tx_params):
            seen["tx_params"] = tx_params
            return {"from": tx_params["from"], "gas": tx_params["gas"]}

    class FakeContract:
        def __init__(self):
            self.functions = SimpleNamespace(issueCertificate=lambda *args, **kwargs: FakeContractFunction("issueCertificate"))

    class FakeEth:
        chain_id = 31337

        def contract(self, address, abi):
            seen["contract_address"] = address
            return FakeContract()

        def get_transaction_count(self, address):
            seen["nonce_address"] = address
            return 7

        def send_raw_transaction(self, raw_tx):
            seen["raw_tx"] = raw_tx
            return b"\xde\xf4\x56"

        def wait_for_transaction_receipt(self, tx_hash, timeout):
            seen["tx_hash"] = tx_hash
            seen["timeout"] = timeout
            return {"transactionHash": tx_hash, "blockNumber": 42, "status": 1}

    class FakeWeb3:
        @staticmethod
        def HTTPProvider(url):
            return url

        @staticmethod
        def to_checksum_address(address):
            return address

        @staticmethod
        def to_hex(value):
            return "0xdef456" if isinstance(value, bytes) else value

        def __init__(self, provider):
            self.provider = provider
            self.eth = FakeEth()

        def is_connected(self):
            return True

    monkeypatch.setattr("app.services.blockchain.get_settings", lambda: SimpleNamespace(
        blockchain_rpc_url="http://localhost:8545",
        blockchain_private_key="0x1234",
        verificert_contract_address="0x1111111111111111111111111111111111111111",
        blockchain_network_name="hardhat-local",
        blockchain_tx_timeout_seconds=120,
        blockchain_gas_limit=750000,
    ))
    monkeypatch.setattr("app.services.blockchain.Web3", FakeWeb3)
    monkeypatch.setattr(
        "app.services.blockchain.Account",
        SimpleNamespace(from_key=lambda private_key: SimpleNamespace(address="0xabc", sign_transaction=lambda tx: SimpleNamespace(raw_transaction=b"signed-raw-tx"))),
    )

    from app.services.blockchain import BlockchainService

    service = BlockchainService()
    receipt = service.issue_certificate("CERT-123", "0x" + "a" * 64, None, "ipfs://metadata")

    assert receipt.transaction_hash == "0xdef456"
    assert receipt.block_number == 42
    assert receipt.contract_address == "0x1111111111111111111111111111111111111111"
    assert seen["tx_params"]["from"] == "0xabc"
    assert seen["raw_tx"] == b"signed-raw-tx"
    assert seen["timeout"] == 120


def test_resolves_signer_by_issuer_wallet(monkeypatch):
    issuer = Account.create()
    other = Account.create()

    class FakeWeb3:
        @staticmethod
        def HTTPProvider(url):
            return url

        @staticmethod
        def to_checksum_address(address):
            return address

        def __init__(self, provider):
            self.eth = SimpleNamespace(contract=lambda address, abi: SimpleNamespace())

        def is_connected(self):
            return True

    monkeypatch.setattr("app.services.blockchain.get_settings", lambda: SimpleNamespace(
        blockchain_rpc_url="http://localhost:8545",
        blockchain_private_key=None,
        abc_academy_private_key=issuer.key.hex(),
        abc_academy_wallet_address=issuer.address,
        northbridge_private_key=other.key.hex(),
        northbridge_wallet_address=other.address,
        cloudskills_private_key=None,
        cloudskills_wallet_address=None,
        brightpath_private_key=None,
        brightpath_wallet_address=None,
        techbridge_private_key=None,
        techbridge_wallet_address=None,
        verificert_contract_address="0x1111111111111111111111111111111111111111",
    ))
    monkeypatch.setattr("app.services.blockchain.Web3", FakeWeb3)

    from app.services.blockchain import BlockchainService

    service = BlockchainService()
    assert service.get_signer_for_issuer(issuer.address).address == issuer.address


def test_missing_or_mismatched_issuer_signer_fails_safely(monkeypatch):
    configured = Account.create()
    requested = Account.create()

    class FakeWeb3:
        @staticmethod
        def HTTPProvider(url):
            return url

        @staticmethod
        def to_checksum_address(address):
            return address

        def __init__(self, provider):
            self.eth = SimpleNamespace(contract=lambda address, abi: SimpleNamespace())

        def is_connected(self):
            return True

    monkeypatch.setattr("app.services.blockchain.get_settings", lambda: SimpleNamespace(
        blockchain_rpc_url="http://localhost:8545",
        blockchain_private_key=None,
        abc_academy_private_key=configured.key.hex(),
        abc_academy_wallet_address=requested.address,
        northbridge_private_key=None,
        northbridge_wallet_address=None,
        cloudskills_private_key=None,
        cloudskills_wallet_address=None,
        brightpath_private_key=None,
        brightpath_wallet_address=None,
        techbridge_private_key=None,
        techbridge_wallet_address=None,
        verificert_contract_address="0x1111111111111111111111111111111111111111",
    ))
    monkeypatch.setattr("app.services.blockchain.Web3", FakeWeb3)

    from app.services.blockchain import BlockchainService

    service = BlockchainService()
    try:
        service.get_signer_for_issuer(requested.address)
    except ValueError as exc:
        assert "does not match" in str(exc)
    else:
        raise AssertionError("A mismatched issuer key must be rejected")

    try:
        service.get_signer_for_issuer(Account.create().address)
    except ValueError as exc:
        assert "No blockchain signer" in str(exc)
    else:
        raise AssertionError("An unconfigured issuer wallet must be rejected")
