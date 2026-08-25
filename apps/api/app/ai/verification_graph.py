from typing import TypedDict

try:
    from langgraph.graph import END, START, StateGraph
except Exception:  # pragma: no cover
    END = START = None
    StateGraph = None

from app.schemas.domain import VerificationRiskAssessment
from app.services.ai_review import analyze_certificate_document


class VerificationState(TypedDict, total=False):
    certificate_id: str
    hash_match: bool
    issuer_match: bool
    blockchain_record_found: bool
    revoked: bool
    expired: bool
    metadata_match: bool
    extracted_metadata: dict
    ai_available: bool
    ai_issues: list[str]
    ai_notes: list[str]
    document_bytes: bytes | None
    document_content_type: str | None
    expected_metadata: dict
    risk: VerificationRiskAssessment


def _extract_metadata(state: VerificationState) -> VerificationState:
    if "metadata_match" in state:
        return state
    document_bytes = state.get("document_bytes")
    if not document_bytes:
        state["ai_available"] = False
        state["metadata_match"] = True
        state["extracted_metadata"] = {}
        state["ai_issues"] = []
        state["ai_notes"] = []
        return state
    review = analyze_certificate_document(document_bytes, state.get("document_content_type") or "application/pdf", state.get("expected_metadata", {}))
    state["ai_available"] = review["available"]
    state["metadata_match"] = review["metadata_match"]
    state["extracted_metadata"] = review["extracted_fields"]
    state["ai_issues"] = [*review["discrepancies"], *review["tamper_signals"]]
    state["ai_notes"] = [review["note"]] if review.get("note") else []
    return state


def _visual_consistency_check(state: VerificationState) -> VerificationState:
    return state


def _assess(state: VerificationState) -> VerificationState:
    issues: list[str] = []
    recommendations: list[str] = []
    score = 5
    if not state.get("blockchain_record_found", False):
        issues.append("No blockchain record was found.")
        score = 90
    if not state.get("hash_match", False):
        issues.append("Uploaded document hash does not match the registered hash.")
        recommendations.append("Treat this credential as modified unless the issuer reissues it.")
        score = max(score, 95)
    if state.get("revoked", False):
        issues.append("Certificate has been revoked.")
        score = max(score, 85)
    if state.get("expired", False):
        issues.append("Certificate is expired.")
        score = max(score, 55)
    if not state.get("issuer_match", True):
        issues.append("Issuer metadata does not match the registered issuer.")
        score = max(score, 70)
    if not state.get("metadata_match", True):
        issues.append("AI document review found metadata that does not match the registered certificate.")
        score = max(score, 65)
    issues.extend(state.get("ai_issues", []))
    if not issues:
        recommendations.append("Credential can be accepted with normal due diligence.")
    level = "LOW" if score < 25 else "MEDIUM" if score < 60 else "HIGH" if score < 90 else "CRITICAL"
    facts = [
        f"Certificate ID: {state.get('certificate_id', 'UNKNOWN')}",
        f"Document hash match: {state.get('hash_match', False)}",
    ]
    if state.get("extracted_metadata"):
        facts.append(f"AI-extracted metadata: {state['extracted_metadata']}")
    inferences = ["Risk score is derived from deterministic verification evidence."]
    if state.get("ai_available"):
        inferences.append("Certificate document was cross-checked against the registered record using Gemini multimodal review.")
    state["risk"] = VerificationRiskAssessment(
        risk_score=score,
        risk_level=level,
        hash_match=state.get("hash_match", False),
        issuer_match=state.get("issuer_match", False),
        certificate_id_match=True,
        blockchain_record_found=state.get("blockchain_record_found", False),
        revoked=state.get("revoked", False),
        expired=state.get("expired", False),
        issues=issues,
        recommendations=recommendations,
        facts=facts,
        inferences=inferences,
        unknowns=state.get("ai_notes", []),
        ai_available=state.get("ai_available", False),
        metadata_match=state.get("metadata_match", True),
        extracted_metadata=state.get("extracted_metadata", {}),
        ai_discrepancies=state.get("ai_issues", []),
    )
    return state


def run_verification_graph(state: VerificationState) -> VerificationRiskAssessment:
    if StateGraph is None:
        return _assess(_visual_consistency_check(_extract_metadata(state)))["risk"]
    graph = StateGraph(VerificationState)
    node_fns = {
        "metadata_extraction": _extract_metadata,
        "visual_consistency_check": _visual_consistency_check,
        "risk_assessment": _assess,
    }
    for node in [
        "document_ingestion",
        "metadata_extraction",
        "issuer_check",
        "blockchain_check",
        "hash_check",
        "visual_consistency_check",
        "risk_assessment",
        "final_result",
    ]:
        graph.add_node(node, node_fns.get(node, lambda s: s))
    graph.add_edge(START, "document_ingestion")
    graph.add_edge("document_ingestion", "metadata_extraction")
    graph.add_edge("metadata_extraction", "issuer_check")
    graph.add_edge("issuer_check", "blockchain_check")
    graph.add_edge("blockchain_check", "hash_check")
    graph.add_edge("hash_check", "visual_consistency_check")
    graph.add_edge("visual_consistency_check", "risk_assessment")
    graph.add_edge("risk_assessment", "final_result")
    graph.add_edge("final_result", END)
    return graph.compile().invoke(state)["risk"]
