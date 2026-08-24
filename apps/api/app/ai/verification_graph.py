from typing import TypedDict

try:
    from langgraph.graph import END, START, StateGraph
except Exception:  # pragma: no cover
    END = START = None
    StateGraph = None

from app.schemas.domain import VerificationRiskAssessment


class VerificationState(TypedDict, total=False):
    certificate_id: str
    hash_match: bool
    issuer_match: bool
    blockchain_record_found: bool
    revoked: bool
    expired: bool
    metadata_match: bool
    extracted_metadata: dict
    risk: VerificationRiskAssessment


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
    if not issues:
        recommendations.append("Credential can be accepted with normal due diligence.")
    level = "LOW" if score < 25 else "MEDIUM" if score < 60 else "HIGH" if score < 90 else "CRITICAL"
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
        facts=[
            f"Certificate ID: {state.get('certificate_id', 'UNKNOWN')}",
            f"Document hash match: {state.get('hash_match', False)}",
        ],
        inferences=["Risk score is derived from deterministic verification evidence."],
        unknowns=[],
    )
    return state


def run_verification_graph(state: VerificationState) -> VerificationRiskAssessment:
    if StateGraph is None:
        return _assess(state)["risk"]
    graph = StateGraph(VerificationState)
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
        graph.add_node(node, _assess if node == "risk_assessment" else lambda s: s)
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
