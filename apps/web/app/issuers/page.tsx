"use client";

import { useEffect, useState } from "react";
import { Building2, Search } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { DirectoryIssuer, getIssuerDirectory } from "@/lib/api";

export default function IssuerDirectoryPage() {
  const [issuers, setIssuers] = useState<DirectoryIssuer[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");

  useEffect(() => {
    const handle = setTimeout(() => {
      getIssuerDirectory(q || undefined).then(setIssuers).catch(() => setError("Unable to load the issuer directory from the backend."));
    }, 250);
    return () => clearTimeout(handle);
  }, [q]);

  return (
    <AppShell>
      <h1 className="text-3xl font-bold text-ink">Approved Issuers</h1>
      <p className="mt-2 text-slate-600">Organizations approved to issue VERIFICERT-backed credentials.</p>
      <div className="relative mt-5 max-w-md">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search organizations" className="w-full rounded border border-slate-300 py-2 pl-9 pr-3 text-sm" />
      </div>
      {error && <p className="mt-4 text-red-700">{error}</p>}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {issuers.map((issuer) => (
          <div key={issuer.id} className="rounded-lg border border-slate-200 bg-white p-5 shadow-soft">
            <div className="flex items-center gap-2">
              <Building2 className="h-5 w-5 text-trust" />
              <h2 className="font-semibold text-ink">{issuer.organization}</h2>
            </div>
            {issuer.description && <p className="mt-2 text-sm text-slate-600">{issuer.description}</p>}
            {issuer.website && (
              <a href={issuer.website} target="_blank" rel="noopener noreferrer" className="mt-3 inline-block text-sm font-semibold text-trust">
                {issuer.website}
              </a>
            )}
            <p className="mt-3 truncate font-mono text-xs text-slate-400" title={issuer.wallet_address}>{issuer.wallet_address}</p>
          </div>
        ))}
        {!error && issuers.length === 0 && <p className="text-slate-600">No approved issuers match this search.</p>}
      </div>
    </AppShell>
  );
}
