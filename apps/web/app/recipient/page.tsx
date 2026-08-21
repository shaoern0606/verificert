import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { StatusBadge } from "@/components/status-badge";

export default function RecipientPage() {
  return (
    <AppShell>
      <h1 className="text-3xl font-bold text-ink">My Certificates</h1>
      <div className="mt-6 rounded-lg border border-slate-200 bg-white shadow-soft">
        {["CERT-2026-000001", "CERT-2026-000004", "CERT-2026-000011"].map((id) => (
          <Link key={id} href={`/verify/${id}`} className="flex items-center justify-between border-b border-slate-100 px-5 py-4 last:border-b-0">
            <span className="font-semibold">{id}</span>
            <StatusBadge status="ACTIVE" />
          </Link>
        ))}
      </div>
    </AppShell>
  );
}
