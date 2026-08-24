"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { AuditLog, getAuditLogs } from "@/lib/api";

export default function Page() {
	const [logs, setLogs] = useState<AuditLog[]>([]);
	const [error, setError] = useState<string | null>(null);
	useEffect(() => { const token = window.localStorage.getItem("verificert_token"); if (!token) { setError("Sign in as an admin to load audit logs."); return; } getAuditLogs(token).then(setLogs).catch(() => setError("Unable to load audit logs from the backend.")); }, []);
	return <AppShell><h1 className="text-3xl font-bold">Audit Logs</h1>{error && <p className="mt-4 text-red-700">{error}</p>}<div className="mt-6 overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-soft"><table className="w-full text-left text-sm"><thead><tr className="border-b border-slate-200 text-slate-500"><th className="px-4 py-3">Timestamp</th><th className="px-4 py-3">Action</th><th className="px-4 py-3">Actor</th><th className="px-4 py-3">Certificate</th></tr></thead><tbody>{logs.map((log, index) => <tr key={`${log.timestamp}-${log.action}-${index}`} className="border-b border-slate-100"><td className="px-4 py-3">{new Date(log.timestamp).toLocaleString()}</td><td className="px-4 py-3">{log.action}</td><td className="px-4 py-3">{log.actor}</td><td className="px-4 py-3">{log.certificate_id ?? "-"}</td></tr>)}</tbody></table>{!error && logs.length === 0 && <p className="p-5 text-slate-600">No audit events are recorded.</p>}</div></AppShell>;
}
