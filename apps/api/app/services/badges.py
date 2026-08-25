# Keyed by CertificateStatus (the database's administrative status) — this badge is a cheap,
# uncached-verification "at a glance" indicator, not the full cryptographic verification result.
BADGE_COLORS: dict[str, str] = {
    "ACTIVE": "#0f9d68",
    "REVOKED": "#dc2626",
    "FAILED": "#dc2626",
    "EXPIRED": "#d97706",
    "PENDING": "#64748b",
    "NOT_FOUND": "#64748b",
}

BADGE_LABELS: dict[str, str] = {
    "ACTIVE": "verified",
    "REVOKED": "revoked",
    "FAILED": "failed",
    "EXPIRED": "expired",
    "PENDING": "pending",
    "NOT_FOUND": "not found",
}


def render_badge_svg(status: str) -> str:
    color = BADGE_COLORS.get(status, "#64748b")
    label = BADGE_LABELS.get(status, status.lower())
    left_width, right_width = 76, len(label) * 7 + 20
    total_width = left_width + right_width
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20" role="img" aria-label="VERIFICERT: {label}">
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r"><rect width="{total_width}" height="20" rx="3" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="{left_width}" height="20" fill="#334155"/>
    <rect x="{left_width}" width="{right_width}" height="20" fill="{color}"/>
    <rect width="{total_width}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
    <text x="{left_width / 2}" y="14">VERIFICERT</text>
    <text x="{left_width + right_width / 2}" y="14">{label}</text>
  </g>
</svg>"""
