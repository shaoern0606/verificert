"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { VerificationResult } from "@/components/verification-result";
import { revokeCertificate, verifyCertificate, VerificationResponse } from "@/lib/api";

export default function IssuerCertificateDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [result, setResult] = useState<VerificationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    verifyCertificate(id).then(setResult).catch(() => setError("Unable to load this certificate from the backend."));
  }, [id]);

  async function revoke() {
    const reason = window.prompt("Reason for revocation:");
    if (!reason || reason.trim().length < 6) return;
    setBusy(true);
    try {
      await revokeCertificate(id, reason.trim());
      const refreshed = await verifyCertificate(id);
      setResult(refreshed);
    } catch {
      setError("The certificate could not be revoked.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <Link href="/issuer/certificates" className="text-sm font-semibold text-trust">
            &larr; Back to issued certificates
          </Link>
          <h1 className="mt-2 text-3xl font-bold text-ink">{id}</h1>
        </div>
        {result?.certificate && result.certificate.status !== "REVOKED" && (
          <button type="button" disabled={busy} onClick={revoke} className="rounded border border-red-300 px-4 py-2 text-sm font-semibold text-red-700 disabled:opacity-60">
            {busy ? "Revoking..." : "Revoke certificate"}
          </button>
        )}
      </div>
      {error && <p className="text-red-700">{error}</p>}
      {!error && !result && <p className="text-slate-600">Loading certificate…</p>}
      {result && (
        <>
          {!result.certificate && <p className="mb-4 text-slate-600">This certificate could not be found.</p>}
          <VerificationResult result={result} />
        </>
      )}
    </AppShell>
  );
}
