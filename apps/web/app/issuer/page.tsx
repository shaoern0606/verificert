import Link from "next/link";
import { AppShell } from "@/components/app-shell";

export default function IssuerDashboard() {
  return (
    <AppShell>
      <h1 className="text-3xl font-bold text-ink">Issuer Workspace</h1>
      <div className="mt-6 grid gap-4 md:grid-cols-4">
        {["Certificates issued", "Active", "Expired", "Revoked"].map((item, idx) => (
          <div key={item} className="rounded-lg border border-slate-200 bg-white p-5 shadow-soft">
            <p className="text-sm text-slate-500">{item}</p>
            <p className="mt-2 text-3xl font-bold">{[30, 20, 5, 5][idx]}</p>
          </div>
        ))}
      </div>
      <Link href="/issuer/certificates/new" className="mt-6 inline-flex rounded bg-trust px-4 py-2 font-semibold text-white">Issue Certificate</Link>
    </AppShell>
  );
}
