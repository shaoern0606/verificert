import json
import logging

from app.core.config import get_settings

logger = logging.getLogger("verificert.ai")

_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "extracted_fields": {
            "type": "object",
            "properties": {
                "recipient_name": {"type": "string"},
                "course_name": {"type": "string"},
                "certificate_title": {"type": "string"},
                "certificate_number": {"type": "string"},
                "issuer_organization": {"type": "string"},
            },
        },
        "metadata_match": {"type": "boolean"},
        "discrepancies": {"type": "array", "items": {"type": "string"}},
        "tamper_signals": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["extracted_fields", "metadata_match", "discrepancies", "tamper_signals"],
}

_UNAVAILABLE = {
    "available": False,
    "metadata_match": True,
    "extracted_fields": {},
    "discrepancies": [],
    "tamper_signals": [],
    "note": "AI document review is not configured (missing GOOGLE_API_KEY).",
}


def analyze_certificate_document(document_bytes: bytes, content_type: str, expected: dict) -> dict:
    settings = get_settings()
    if not settings.google_api_key:
        return dict(_UNAVAILABLE)
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.google_api_key)
        prompt = (
            "You are a document review assistant for a certificate verification system. "
            "Look at the attached certificate document and extract the recipient name, course or program name, "
            "certificate title, certificate number, and issuer organization name exactly as they visibly appear. "
            "Then compare them against the expected record and flag any mismatches, plus any visual signs of "
            "tampering such as inconsistent fonts, misalignment, or obvious edits.\n\n"
            f"Expected record: {json.dumps(expected)}"
        )
        response = client.models.generate_content(
            model=settings.google_ai_model,
            contents=[
                types.Part.from_bytes(data=document_bytes, mime_type=content_type or "application/pdf"),
                prompt,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=_RESPONSE_SCHEMA,
                temperature=0,
            ),
        )
        parsed = json.loads(response.text)
        return {
            "available": True,
            "metadata_match": bool(parsed.get("metadata_match", True)),
            "extracted_fields": parsed.get("extracted_fields", {}),
            "discrepancies": parsed.get("discrepancies", []),
            "tamper_signals": parsed.get("tamper_signals", []),
            "note": None,
        }
    except Exception as exc:
        logger.warning("ai_document_review_failed error=%s", exc)
        return {
            "available": False,
            "metadata_match": True,
            "extracted_fields": {},
            "discrepancies": [],
            "tamper_signals": [],
            "note": f"AI document review failed: {exc}",
        }
