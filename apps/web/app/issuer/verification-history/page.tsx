"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { AuditLog, getAuditLogs } from "@/lib/api";

export default function Page() {
	const [logs, setLogs] = useState<AuditLog[]>([]);
	const [error, setError] = useState<string | null>(null);
	useEffect(() => { const token = window.localStorage.getItem("verificert_token"); if (!token) { setError("Sign in as an issuer to load verification history."); return; } getAuditLogs(token).then((items) => setLogs(items.filter((item) => item.action === "VERIFY_CERTIFICATE"))).catch(() => setError("Unable to load verification history from the backend.")); }, []);
	return <AppShell><h1 className="text-3xl font-bold">Verification History</h1>{error && <p className="mt-4 text-red-700">{error}</p>}<div className="mt-6 rounded-lg border border-slate-200 bg-white shadow-soft">{logs.map((log, index) => <div key={`${log.timestamp}-${index}`} className="flex items-center justify-between border-b border-slate-100 px-5 py-4"><span><span className="block font-semibold">{log.certificate_id ?? "Unknown certificate"}</span><span className="text-sm text-slate-500">{new Date(log.timestamp).toLocaleString()}</span></span><span className="text-sm font-semibold">{log.action}</span></div>)}{!error && logs.length === 0 && <p className="p-5 text-slate-600">No verification attempts are recorded.</p>}</div></AppShell>;
}
