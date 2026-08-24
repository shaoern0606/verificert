"use client";

import { useRouter } from "next/navigation";
import { Search, Upload } from "lucide-react";
import { AppShell } from "@/components/app-shell";

export default function VerifyPage() {
  const router = useRouter();
  return (
    <AppShell>
      <section className="mx-auto max-w-3xl rounded-lg border border-slate-200 bg-white p-6 shadow-soft">
        <h1 className="text-3xl font-bold text-ink">Verify a Certificate</h1>
        <form
          className="mt-6 flex gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            const data = new FormData(event.currentTarget);
            const id = String(data.get("certificateId") ?? "").trim();
            if (id) router.push(`/verify/${encodeURIComponent(id)}`);
          }}
        >
          <input name="certificateId" className="min-w-0 flex-1 rounded border border-slate-300 px-3 py-2" placeholder="CERT-2026-000001" />
          <button className="inline-flex items-center gap-2 rounded bg-trust px-4 py-2 font-semibold text-white">
            <Search className="h-4 w-4" />
            Verify
          </button>
        </form>
        <div className="mt-6 rounded border border-dashed border-slate-300 p-5 text-sm text-slate-600">
          <Upload className="mb-3 h-5 w-5" />
          Upload verification is available through <code>/api/verify/upload</code> and compares exact PDF bytes against the blockchain hash.
        </div>
      </section>
    </AppShell>
  );
}
