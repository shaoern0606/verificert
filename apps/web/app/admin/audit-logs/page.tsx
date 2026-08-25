"use client";

import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { AuditLog, getAuditLogs } from "@/lib/api";

const ACTIONS = ["", "LOGIN", "ISSUE_CERTIFICATE", "VERIFY_CERTIFICATE", "REVOKE_CERTIFICATE", "REGISTER_ISSUER", "SUSPEND_ISSUER", "DOWNLOAD_CERTIFICATE", "AI_ANALYSIS"];

export default function Page() {
	const [logs, setLogs] = useState<AuditLog[]>([]);
	const [error, setError] = useState<string | null>(null);
	const [q, setQ] = useState("");
	const [action, setAction] = useState("");

	useEffect(() => {
		const handle = setTimeout(() => {
			getAuditLogs({ q: q || undefined, action: action || undefined }).then(setLogs).catch(() => setError("Unable to load audit logs from the backend."));
		}, 250);
		return () => clearTimeout(handle);
	}, [q, action]);

	return (
		<AppShell>
			<h1 className="text-3xl font-bold">Audit Logs</h1>
			<div className="mt-4 flex flex-wrap gap-3">
				<div className="relative min-w-0 flex-1">
					<Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
					<input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search by certificate ID or actor" className="w-full rounded border border-slate-300 py-2 pl-9 pr-3 text-sm" />
				</div>
				<select value={action} onChange={(e) => setAction(e.target.value)} className="rounded border border-slate-300 px-3 py-2 text-sm">
					{ACTIONS.map((a) => (
						<option key={a} value={a}>{a || "All actions"}</option>
					))}
				</select>
			</div>
			{error && <p className="mt-4 text-red-700">{error}</p>}
			<div className="mt-6 overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-soft">
				<table className="w-full text-left text-sm">
					<thead>
						<tr className="border-b border-slate-200 text-slate-500">
							<th className="px-4 py-3">Timestamp</th>
							<th className="px-4 py-3">Action</th>
							<th className="px-4 py-3">Actor</th>
							<th className="px-4 py-3">Certificate</th>
						</tr>
					</thead>
					<tbody>
						{logs.map((log, index) => (
							<tr key={`${log.timestamp}-${log.action}-${index}`} className="border-b border-slate-100">
								<td className="px-4 py-3">{new Date(log.timestamp).toLocaleString()}</td>
								<td className="px-4 py-3">{log.action}</td>
								<td className="px-4 py-3">{log.actor}</td>
								<td className="px-4 py-3">{log.certificate_id ?? "-"}</td>
							</tr>
						))}
					</tbody>
				</table>
				{!error && logs.length === 0 && <p className="p-5 text-slate-600">No audit events match this search.</p>}
			</div>
		</AppShell>
	);
}
