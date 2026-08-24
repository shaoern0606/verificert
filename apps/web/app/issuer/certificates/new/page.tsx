"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { API_URL, getMyIssuer } from "@/lib/api";

export default function NewCertificatePage() {
  const router = useRouter();
  const [issuerId, setIssuerId] = useState("");
  const [issuerStatus, setIssuerStatus] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [signedIn, setSignedIn] = useState(false);
  useEffect(() => { const token = window.localStorage.getItem("verificert_token"); if (!token) return; setSignedIn(true); getMyIssuer(token).then((issuer) => { setIssuerId(issuer.id); setIssuerStatus(issuer.status); }).catch(() => setMessage("Unable to load the issuer profile.")); }, []);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = window.localStorage.getItem("verificert_token");
    if (!token) { setMessage("Sign in as an issuer before issuing a certificate."); return; }
    const form = new FormData(event.currentTarget);
    form.set("issuer_id", issuerId);
    let response: Response;
    try {
      response = await fetch(`${API_URL}/api/certificates`, { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: form });
    } catch {
      setMessage("The API is unavailable. Check that the backend is running.");
      return;
    }
    if (!response.ok) {
      const body = await response.json().catch(() => null);
      const detail = typeof body?.detail?.error?.message === "string" ? body.detail.error.message : null;
      setMessage(detail ?? "The certificate could not be issued and registered.");
      return;
    }
    const result = await response.json();
    router.push(`/verify/${result.certificate_id}`);
  }
  return (
    <AppShell>
      <section className="max-w-4xl rounded-lg border border-slate-200 bg-white p-6 shadow-soft">
        <h1 className="text-3xl font-bold text-ink">Issue Certificate</h1>
        {!signedIn && <div className="mt-4 rounded border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">Sign in with an approved issuer account before issuing a certificate. <Link href="/login" className="font-semibold underline">Sign in</Link> or <Link href="/register" className="font-semibold underline">register</Link>.</div>}
        {signedIn && issuerStatus && <p className="mt-4 text-sm text-slate-600">Issuer account status: <span className="font-semibold text-ink">{issuerStatus}</span>{issuerStatus !== "APPROVED" && " Issuance is disabled until an admin approves this account."}</p>}
        <form className="mt-6 grid gap-4 md:grid-cols-2" onSubmit={submit}>
          {[['Recipient name', 'recipient_name'], ['Recipient email', 'recipient_email'], ['Course/program name', 'course_name'], ['Certificate title', 'certificate_title'], ['Issue date', 'issue_date'], ['Expiry date', 'expiry_date'], ['Certificate number', 'certificate_number']].map(([label, name]) => (
            <label key={label} className="text-sm font-medium text-slate-700">
              {label}
              <input name={name} type={name.includes('date') ? 'datetime-local' : name.includes('email') ? 'email' : 'text'} required={name !== 'expiry_date'} className="mt-1 w-full rounded border border-slate-300 px-3 py-2" placeholder={label} />
            </label>
          ))}
          <label className="md:col-span-2 text-sm font-medium text-slate-700">
            Certificate file
            <input name="file" type="file" accept="application/pdf,image/jpeg,image/png,image/gif,image/webp" required className="mt-1 w-full rounded border border-slate-300 px-3 py-2" />
          </label>
          {message && <p className="text-sm text-red-700 md:col-span-2">{message}</p>}
          <button disabled={!issuerId} className="rounded bg-trust px-4 py-2 font-semibold text-white disabled:opacity-60 md:w-fit">Issue and Register</button>
        </form>
      </section>
    </AppShell>
  );
}
