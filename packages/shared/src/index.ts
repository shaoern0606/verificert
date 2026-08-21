export type VerificationState = "VERIFIED" | "INVALID" | "REVOKED" | "EXPIRED" | "NOT_FOUND" | "PENDING" | "SUSPICIOUS";

export const verificationRules = [
  "certificate_exists",
  "issuer_recognized",
  "blockchain_record_found",
  "hash_matches",
  "not_revoked",
  "not_expired",
  "metadata_matches",
  "ai_risk_reviewed",
] as const;

export type CertificateSummary = {
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
