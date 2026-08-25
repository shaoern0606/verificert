"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { StatusBadge } from "@/components/status-badge";
import { getMyIssuer, IssuerProfile } from "@/lib/api";

export default function IssuerSettingsPage() {
  const [profile, setProfile] = useState<IssuerProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMyIssuer()
      .then(setProfile)
      .catch(() => setError("Sign in as an issuer, and make sure an issuer profile is linked to this account."));
  }, []);

  return (
    <AppShell>
      <h1 className="text-3xl font-bold text-ink">Issuer Settings</h1>
      {error && <p className="mt-4 text-red-700">{error}</p>}
      {!error && !profile && <p className="mt-4 text-slate-600">Loading profile…</p>}
      {profile && (
        <div className="mt-6 max-w-2xl rounded-lg border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-ink">{profile.organization}</h2>
            <StatusBadge status={profile.status} />
          </div>
          {profile.status !== "APPROVED" && (
            <p className="mt-2 text-sm text-amber-800">
              {profile.status === "PENDING" && "This issuer profile is awaiting admin approval. Certificate issuance is disabled until then."}
              {profile.status === "SUSPENDED" && "This issuer has been suspended by an admin. Certificate issuance is disabled."}
              {profile.status === "REJECTED" && "This issuer application was rejected."}
            </p>
          )}
          <dl className="mt-6 grid gap-4 sm:grid-cols-2">
            <Field label="Contact person" value={profile.contact_person} />
            <Field label="Contact email" value={profile.email} />
            <Field label="Website" value={profile.website ?? "—"} />
            <Field label="Registration number" value={profile.registration_number ?? "—"} />
            <Field label="Wallet address" value={profile.wallet_address} mono />
            <Field label="Description" value={profile.description ?? "—"} />
          </dl>
          <p className="mt-6 rounded border border-slate-200 bg-panel p-3 text-xs text-slate-500">
            This information is read-only for now — updating an issuer profile isn&apos;t supported yet. Contact an admin if these details need to change.
          </p>
        </div>
      )}
    </AppShell>
  );
}

function Field({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className={`mt-1 break-words text-sm font-semibold text-slate-900 ${mono ? "font-mono" : ""}`}>{value}</dd>
    </div>
  );
}
