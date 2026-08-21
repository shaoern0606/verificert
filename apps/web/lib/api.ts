export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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

export async function getDashboard(): Promise<{ cards: Record<string, number>; charts: Record<string, { name: string; value: number }[]> }> {
  const res = await fetch(`${API_URL}/api/dashboard/admin`, {
    cache: "no-store",
    headers: { Authorization: `Bearer ${process.env.DEMO_ADMIN_TOKEN ?? ""}` },
  });
  if (!res.ok) {
    return {
      cards: { total_certificates: 30, active: 20, expired: 5, revoked: 5, registered_issuers: 5, verification_attempts: 12 },
      charts: { certificates_by_status: [{ name: "ACTIVE", value: 20 }, { name: "EXPIRED", value: 5 }, { name: "REVOKED", value: 5 }] },
    };
  }
  return res.json();
}
