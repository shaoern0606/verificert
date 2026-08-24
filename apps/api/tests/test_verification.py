from app.ai.verification_graph import run_verification_graph
from app.services.hashing import sha256_bytes


def test_sha256_uses_exact_bytes():
    assert sha256_bytes(b"certificate") != sha256_bytes(b"certificate ")


def test_ai_marks_hash_mismatch_critical():
    result = run_verification_graph(
        {
            "certificate_id": "CERT-2026-000001",
            "hash_match": False,
            "issuer_match": True,
            "blockchain_record_found": True,
            "revoked": False,
            "expired": False,
        }
    )
    assert result.risk_level == "CRITICAL"
    assert result.risk_score >= 90
