export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type CurrentUser = { email: string; full_name: string; role: "ADMIN" | "ISSUER" | "RECIPIENT" | "VERIFIER" };
export type Issuer = { id: string; organization: string; email: string; wallet_address: string; status: string };

export type CertificateListItem = {
  certificate_id: string;
  certificate_number: string;
  title: string;
  program: string;
  recipient: string;
  issuer: string;
  issued: string;
  expires: string | null;
  status: string;
  verification_url: string;
  transaction_hash: string | null;
};

export type VerificationResponse = {
  status: "VERIFIED" | "INVALID" | "REVOKED" | "EXPIRED" | "NOT_FOUND" | "PENDING" | "SUSPICIOUS";
  certificate_id: string;
  decisive_reason: string;
  checks: Record<string, boolean>;
  certificate: null | {
    certificate_id: string;
    recipient: string;
    program: string;
    issuer: string;
    issued: string;
    expires: string | null;
    status: string;
    document_hash: string;
    verification_url: string;
    transaction_hash: string | null;
  };
  ai: null | {
    risk_score: number;
    risk_level: string;
    issues: string[];
    recommendations: string[];
    facts: string[];
    inferences: string[];
    unknowns: string[];
  };
  technical_details: Record<string, unknown>;
};

export async function verifyCertificate(certificateId: string): Promise<VerificationResponse> {
  const res = await fetch(`${API_URL}/api/verify/${encodeURIComponent(certificateId)}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Verification request failed");
  return res.json();
}

export async function getDashboard(token: string): Promise<{ cards: Record<string, number>; charts: Record<string, { name: string; value: number }[]> }> {
  const res = await fetch(`${API_URL}/api/dashboard/admin`, {
    cache: "no-store",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new Error("Dashboard request failed");
  }
  return res.json();
}

async function authenticated<T>(path: string, token: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { ...options, cache: "no-store", headers: { ...options.headers, Authorization: `Bearer ${token}` } });
  if (!res.ok) throw new Error("Backend request failed");
  return res.json();
}

export function getCurrentUser(token: string): Promise<CurrentUser> {
  return authenticated("/api/auth/me", token);
}

export function getIssuers(token: string): Promise<Issuer[]> {
  return authenticated("/api/issuers", token);
}

export function updateIssuerStatus(token: string, issuerId: string, action: "approve" | "suspend"): Promise<{ id: string; status: string }> {
  return authenticated(`/api/issuers/${issuerId}/${action}`, token, { method: "POST" });
}

export function getIssuerDashboard(token: string): Promise<{ cards: Record<string, number>; certificates: CertificateListItem[] }> {
  return authenticated("/api/dashboard/issuer", token);
}

export function getCertificates(token: string): Promise<CertificateListItem[]> {
  return authenticated("/api/certificates", token);
}

export function getRecipientCertificates(token: string): Promise<CertificateListItem[]> {
  return authenticated("/api/certificates/recipient", token);
}

export async function revokeCertificate(token: string, certificateId: string, reason: string): Promise<{ certificate_id: string; status: string; revocation_reason: string }> {
  return authenticated(`/api/certificates/${encodeURIComponent(certificateId)}/revoke`, token, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
  });
}

export function getMyIssuer(token: string): Promise<{ id: string; organization: string; status: string }> {
  return authenticated("/api/issuers/me", token);
}

export type AuditLog = { timestamp: string; actor: string; role: string; action: string; certificate_id: string | null; metadata: Record<string, unknown> };

export function getAuditLogs(token: string): Promise<AuditLog[]> {
  return authenticated("/api/audit-logs", token);
}
