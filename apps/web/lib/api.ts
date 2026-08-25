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

export async function verifyByFile(file: File): Promise<VerificationResponse> {
  const form = new FormData();
  form.set("file", file);
  const res = await fetch(`${API_URL}/api/verify/upload`, { method: "POST", cache: "no-store", body: form });
  if (!res.ok) throw new Error("Upload verification request failed");
  return res.json();
}

export function getDashboard(): Promise<{ cards: Record<string, number>; charts: Record<string, { name: string; value: number }[]> }> {
  return authenticated("/api/dashboard/admin");
}

async function authenticated<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { ...options, cache: "no-store", credentials: "include", headers: { ...options.headers } });
  if (!res.ok) throw new Error("Backend request failed");
  return res.json();
}

export function getCurrentUser(): Promise<CurrentUser> {
  return authenticated("/api/auth/me");
}

export async function logout(): Promise<void> {
  await fetch(`${API_URL}/api/auth/logout`, { method: "POST", credentials: "include" });
}

function qs(params: Record<string, string | undefined>): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== "");
  if (entries.length === 0) return "";
  return `?${new URLSearchParams(entries as [string, string][]).toString()}`;
}

export function getIssuers(params: { q?: string; status?: string } = {}): Promise<Issuer[]> {
  return authenticated(`/api/issuers${qs(params)}`);
}

export function updateIssuerStatus(issuerId: string, action: "approve" | "suspend"): Promise<{ id: string; status: string }> {
  return authenticated(`/api/issuers/${issuerId}/${action}`, { method: "POST" });
}

export type DirectoryIssuer = { id: string; organization: string; website: string | null; description: string | null; wallet_address: string };

export async function getIssuerDirectory(q?: string): Promise<DirectoryIssuer[]> {
  const res = await fetch(`${API_URL}/api/issuers/directory${qs({ q })}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Directory request failed");
  return res.json();
}

export function getIssuerDashboard(): Promise<{ cards: Record<string, number>; certificates: CertificateListItem[] }> {
  return authenticated("/api/dashboard/issuer");
}

export function getCertificates(params: { q?: string; status?: string } = {}): Promise<CertificateListItem[]> {
  return authenticated(`/api/certificates${qs(params)}`);
}

export async function bulkIssueCertificates(issuerId: string, file: File): Promise<{ issued: { row: number; certificate_id: string; recipient_email: string }[]; failed: { row: number; error: string }[] }> {
  const form = new FormData();
  form.set("issuer_id", issuerId);
  form.set("file", file);
  const res = await fetch(`${API_URL}/api/certificates/bulk`, { method: "POST", credentials: "include", body: form });
  if (!res.ok) throw new Error("Bulk issuance request failed");
  return res.json();
}

export type ApiKeySummary = { id: string; label: string; prefix: string; created_by: string; created_at: string; last_used_at: string | null; revoked: boolean };

export function listApiKeys(): Promise<ApiKeySummary[]> {
  return authenticated("/api/admin/api-keys");
}

export function createApiKey(label: string): Promise<{ id: string; label: string; key: string; prefix: string }> {
  return authenticated("/api/admin/api-keys", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ label }) });
}

export function revokeApiKey(id: string): Promise<{ id: string; revoked: boolean }> {
  return authenticated(`/api/admin/api-keys/${id}`, { method: "DELETE" });
}

export function getRecipientCertificates(): Promise<CertificateListItem[]> {
  return authenticated("/api/certificates/recipient");
}

export async function revokeCertificate(certificateId: string, reason: string): Promise<{ certificate_id: string; status: string; revocation_reason: string }> {
  return authenticated(`/api/certificates/${encodeURIComponent(certificateId)}/revoke`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
  });
}

export type IssuerProfile = {
  id: string;
  organization: string;
  status: string;
  contact_person: string;
  email: string;
  wallet_address: string;
  description: string | null;
  website: string | null;
  registration_number: string | null;
};

export function getMyIssuer(): Promise<IssuerProfile> {
  return authenticated("/api/issuers/me");
}

export type AuditLog = { timestamp: string; actor: string; role: string; action: string; certificate_id: string | null; metadata: Record<string, unknown> };

export function getAuditLogs(params: { q?: string; action?: string } = {}): Promise<AuditLog[]> {
  return authenticated(`/api/audit-logs${qs(params)}`);
}
