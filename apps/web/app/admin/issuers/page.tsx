"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { getIssuers, Issuer, updateIssuerStatus } from "@/lib/api";

export default function Page() {
	const [issuers, setIssuers] = useState<Issuer[]>([]);
	const [error, setError] = useState<string | null>(null);
	const [busy, setBusy] = useState<string | null>(null);
	useEffect(() => { const token = window.localStorage.getItem("verificert_token"); if (!token) { setError("Sign in as an admin to review issuers."); return; } getIssuers(token).then(setIssuers).catch(() => setError("Unable to load issuers from the backend.")); }, []);
	async function changeStatus(issuer: Issuer, action: "approve" | "suspend") {
		const token = window.localStorage.getItem("verificert_token"); if (!token) return;
		setBusy(issuer.id);
		try { const updated = await updateIssuerStatus(token, issuer.id, action); setIssuers((items) => items.map((item) => item.id === issuer.id ? { ...item, status: updated.status } : item)); } catch { setError("The issuer status could not be updated on the backend."); } finally { setBusy(null); }
	}
	return <AppShell><h1 className="text-3xl font-bold">Issuer Management</h1><p className="mt-3 text-slate-600">Approve, suspend, and review issuer applications.</p>{error && <p className="mt-4 text-red-700">{error}</p>}<div className="mt-6 overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-soft"><table className="w-full text-left text-sm"><thead><tr className="border-b border-slate-200 text-slate-500"><th className="px-4 py-3">Organization</th><th className="px-4 py-3">Contact</th><th className="px-4 py-3">Wallet</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Review</th></tr></thead><tbody>{issuers.map((issuer) => <tr key={issuer.id} className="border-b border-slate-100"><td className="px-4 py-3 font-semibold">{issuer.organization}</td><td className="px-4 py-3">{issuer.email}</td><td className="px-4 py-3 font-mono text-xs">{issuer.wallet_address}</td><td className="px-4 py-3">{issuer.status}</td><td className="px-4 py-3"><span className="flex gap-2">{issuer.status !== "APPROVED" && <button disabled={busy === issuer.id} onClick={() => changeStatus(issuer, "approve")} className="rounded bg-trust px-3 py-1 font-semibold text-white disabled:opacity-60">Approve</button>}{issuer.status !== "SUSPENDED" && <button disabled={busy === issuer.id} onClick={() => changeStatus(issuer, "suspend")} className="rounded border border-red-300 px-3 py-1 font-semibold text-red-700 disabled:opacity-60">Suspend</button>}</span></td></tr>)}</tbody></table>{!error && issuers.length === 0 && <p className="p-5 text-slate-600">No issuer applications are recorded.</p>}</div></AppShell>;
}
