"use client";

import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { StatusBadge } from "@/components/status-badge";
import { CertificateListItem, getRecipientCertificates } from "@/lib/api";
import { useEffect, useState } from "react";

export default function RecipientPage() {
  const [certificates, setCertificates] = useState<CertificateListItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    getRecipientCertificates().then(setCertificates).catch(() => setError("Unable to load certificates from the backend."));
  }, []);
  return (
    <AppShell>
      <h1 className="text-3xl font-bold text-ink">My Certificates</h1>
      {error && <p className="mt-4 text-red-700">{error}</p>}
      <div className="mt-6 rounded-lg border border-slate-200 bg-white shadow-soft">
        {certificates.map((certificate) => (
          <Link key={certificate.certificate_id} href={`/verify/${certificate.certificate_id}`} className="flex items-center justify-between border-b border-slate-100 px-5 py-4 last:border-b-0">
            <span><span className="block font-semibold">{certificate.certificate_id}</span><span className="text-sm text-slate-500">{certificate.program}</span></span>
            <StatusBadge status={certificate.status} />
          </Link>
        ))}
        {!error && certificates.length === 0 && <p className="p-5 text-slate-600">No certificates are linked to this account.</p>}
      </div>
    </AppShell>
  );
}
