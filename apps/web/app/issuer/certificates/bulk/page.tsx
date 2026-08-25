"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { Download, Upload } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { bulkIssueCertificates, getMyIssuer } from "@/lib/api";

const TEMPLATE_CSV = "recipient_name,recipient_email,course_name,certificate_title,certificate_number,issue_date,expiry_date,description\nJane Doe,jane.doe@example.com,Advanced Python Programming,Certificate of Completion,CN-2026-001,2026-01-15,,\n";

type BulkResult = { issued: { row: number; certificate_id: string; recipient_email: string }[]; failed: { row: number; error: string }[] };

export default function BulkIssueCertificatesPage() {
  const [issuerId, setIssuerId] = useState("");
  const [issuerStatus, setIssuerStatus] = useState<string | null>(null);
  const [signedIn, setSignedIn] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [result, setResult] = useState<BulkResult | null>(null);

  useEffect(() => {
    getMyIssuer().then((issuer) => { setSignedIn(true); setIssuerId(issuer.id); setIssuerStatus(issuer.status); }).catch(() => setSignedIn(false));
  }, []);

  function downloadTemplate() {
    const blob = new Blob([TEMPLATE_CSV], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "verificert-bulk-template.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const file = form.get("file") as File | null;
    if (!file || file.size === 0) { setMessage("Choose a CSV file to upload."); return; }
    setBusy(true);
    setMessage(null);
    setResult(null);
    try {
      const response = await bulkIssueCertificates(issuerId, file);
      setResult(response);
      setMessage(`Issued ${response.issued.length} of ${response.issued.length + response.failed.length} certificate(s).`);
    } catch {
      setMessage("The bulk upload could not be processed. Check that the API is running.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell>
      <Link href="/issuer/certificates" className="text-sm font-semibold text-trust">&larr; Back to issued certificates</Link>
      <h1 className="mt-2 text-3xl font-bold text-ink">Bulk Issue Certificates</h1>
      <section className="mt-6 max-w-2xl rounded-lg border border-slate-200 bg-white p-6 shadow-soft">
        {!signedIn && <div className="rounded border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">Sign in with an approved issuer account before issuing certificates. <Link href="/login" className="font-semibold underline">Sign in</Link></div>}
        {signedIn && issuerStatus && issuerStatus !== "APPROVED" && <p className="text-sm text-amber-800">Issuance is disabled until an admin approves this account. Current status: {issuerStatus}</p>}
        <p className="text-sm text-slate-600">
          Upload a CSV of recipients to issue many certificates at once. Each row generates its own certificate PDF (with an embedded verification QR code), hashes it, and registers it on-chain — exactly like issuing one at a time.
        </p>
        <button type="button" onClick={downloadTemplate} className="mt-4 inline-flex items-center gap-2 rounded border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700">
          <Download className="h-4 w-4" />
          Download CSV template
        </button>
        <form onSubmit={submit} className="mt-6">
          <label className="block text-sm font-medium text-slate-700">
            CSV file
            <input name="file" type="file" accept=".csv,text/csv" required className="mt-1 block w-full rounded border border-slate-300 px-3 py-2" />
          </label>
          {message && <p className="mt-4 text-sm text-slate-700">{message}</p>}
          <button disabled={!issuerId || busy} className="mt-4 inline-flex items-center gap-2 rounded bg-trust px-4 py-2 font-semibold text-white disabled:opacity-60">
            <Upload className="h-4 w-4" />
            {busy ? "Issuing certificates..." : "Upload and issue"}
          </button>
        </form>
      </section>
      {result && (
        <section className="mt-6 grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-slate-200 bg-white shadow-soft">
            <h2 className="border-b border-slate-200 px-4 py-3 font-semibold text-emerald-700">Issued ({result.issued.length})</h2>
            {result.issued.map((row) => (
              <div key={row.row} className="border-b border-slate-100 px-4 py-2 text-sm last:border-b-0">
                <Link href={`/verify/${row.certificate_id}`} className="font-semibold text-trust">{row.certificate_id}</Link>
                <span className="ml-2 text-slate-500">{row.recipient_email}</span>
              </div>
            ))}
            {result.issued.length === 0 && <p className="p-4 text-sm text-slate-500">None.</p>}
          </div>
          <div className="rounded-lg border border-slate-200 bg-white shadow-soft">
            <h2 className="border-b border-slate-200 px-4 py-3 font-semibold text-red-700">Failed ({result.failed.length})</h2>
            {result.failed.map((row) => (
              <div key={row.row} className="border-b border-slate-100 px-4 py-2 text-sm last:border-b-0">
                <span className="font-semibold">Row {row.row}</span>
                <span className="ml-2 text-slate-600">{row.error}</span>
              </div>
            ))}
            {result.failed.length === 0 && <p className="p-4 text-sm text-slate-500">None.</p>}
          </div>
        </section>
      )}
    </AppShell>
  );
}
