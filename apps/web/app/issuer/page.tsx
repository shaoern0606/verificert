"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { getIssuerDashboard, getMyIssuer } from "@/lib/api";

export default function IssuerDashboard() {
  const [data, setData] = useState<{ cards: Record<string, number> } | null>(null);
  const [profile, setProfile] = useState<{ organization: string; status: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    Promise.all([getIssuerDashboard(), getMyIssuer()]).then(([dashboard, issuer]) => { setData(dashboard); setProfile(issuer); }).catch(() => setError("Unable to load workspace data from the backend."));
  }, []);
  return (
    <AppShell>
      <h1 className="text-3xl font-bold text-ink">Issuer Workspace</h1>
      {profile && <p className="mt-2 text-sm text-slate-600">{profile.organization} · Account status: <span className="font-semibold text-ink">{profile.status}</span></p>}
      {error && <div className="mt-6 rounded border border-red-200 bg-red-50 p-4 text-red-700">{error}</div>}
      <div className="mt-6 grid gap-4 md:grid-cols-4">
        {[['Certificates issued', 'total_certificates'], ['Active', 'active'], ['Expired', 'expired'], ['Revoked', 'revoked']].map(([item, key]) => (
          <div key={item} className="rounded-lg border border-slate-200 bg-white p-5 shadow-soft">
            <p className="text-sm text-slate-500">{item}</p>
            <p className="mt-2 text-3xl font-bold">{data?.cards[key] ?? "-"}</p>
          </div>
        ))}
      </div>
      <div className="mt-6 flex flex-wrap gap-3">
        <Link href="/issuer/certificates/new" className="inline-flex rounded bg-trust px-4 py-2 font-semibold text-white">Issue Certificate</Link>
        <Link href="/issuer/certificates/bulk" className="inline-flex rounded border border-slate-300 bg-white px-4 py-2 font-semibold text-slate-700">Bulk Issue (CSV)</Link>
        <Link href="/issuer/certificates" className="inline-flex rounded border border-slate-300 bg-white px-4 py-2 font-semibold text-slate-700">View Issued Certificates</Link>
        <Link href="/issuer/verification-history" className="inline-flex rounded border border-slate-300 bg-white px-4 py-2 font-semibold text-slate-700">Verification History</Link>
        <Link href="/issuer/settings" className="inline-flex rounded border border-slate-300 bg-white px-4 py-2 font-semibold text-slate-700">Issuer Settings</Link>
      </div>
    </AppShell>
  );
}
