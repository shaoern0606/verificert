import Link from "next/link";
import { Activity, FileCheck2, KeyRound, ShieldCheck } from "lucide-react";
import { AppShell } from "@/components/app-shell";

const cards = [
  ["Issue", "Create hash-anchored certificates with QR verification URLs.", FileCheck2],
  ["Verify", "Confirm issuer, blockchain record, file integrity, status, and AI risk.", ShieldCheck],
  ["Revoke", "Preserve the historical record while making invalid credentials obvious.", KeyRound],
  ["Monitor", "Track issuance, verification activity, revocations, and audit events.", Activity],
];

export default function Home() {
  return (
    <AppShell>
      <section className="grid gap-8 lg:grid-cols-[1.05fr_0.95fr]">
        <div>
          <p className="text-sm font-semibold uppercase text-trust">Digital Credential Trust Platform</p>
          <h1 className="mt-3 max-w-3xl text-5xl font-bold leading-tight text-ink">VERIFICERT</h1>
          <p className="mt-5 max-w-2xl text-lg text-slate-700">
            Verify that a digital credential was genuinely issued, has not been altered, and is still valid.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link className="rounded bg-trust px-4 py-2 font-semibold text-white" href="/verify/CERT-2026-000001">Open Demo Verification</Link>
            <Link className="rounded border border-slate-300 bg-white px-4 py-2 font-semibold text-slate-800" href="/issuer/certificates/new">Issue Certificate</Link>
          </div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-soft">
          <div className="grid gap-3 sm:grid-cols-2">
            {cards.map(([title, text, Icon]) => (
              <div key={title as string} className="rounded border border-slate-200 p-4">
                <Icon className="h-6 w-6 text-trust" />
                <h2 className="mt-4 font-semibold text-ink">{title as string}</h2>
                <p className="mt-2 text-sm text-slate-600">{text as string}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </AppShell>
  );
}
