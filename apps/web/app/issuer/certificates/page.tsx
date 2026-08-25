"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { StatusBadge } from "@/components/status-badge";
import { CertificateListItem, getCertificates, revokeCertificate } from "@/lib/api";

const STATUSES = ["", "ACTIVE", "EXPIRED", "REVOKED", "PENDING", "FAILED"];

export default function Page() {
	const [certificates, setCertificates] = useState<CertificateListItem[]>([]);
	const [error, setError] = useState<string | null>(null);
	const [busy, setBusy] = useState<string | null>(null);
	const [q, setQ] = useState("");
	const [status, setStatus] = useState("");

	async function revoke(cert: CertificateListItem) {
		const reason = window.prompt("Reason for revocation:");
		if (!reason || reason.trim().length < 6) return;
		setBusy(cert.certificate_id);
		try { await revokeCertificate(cert.certificate_id, reason.trim()); setCertificates((items) => items.map((item) => item.certificate_id === cert.certificate_id ? { ...item, status: "REVOKED" } : item)); } catch { setError("The certificate could not be revoked."); } finally { setBusy(null); }
	}

	useEffect(() => {
		const handle = setTimeout(() => {
			getCertificates({ q: q || undefined, status: status || undefined }).then(setCertificates).catch(() => setError("Unable to load certificates from the backend."));
		}, 250);
		return () => clearTimeout(handle);
	}, [q, status]);

	return (
		<AppShell>
			<h1 className="text-3xl font-bold">Issued Certificates</h1>
			<div className="mt-4 flex flex-wrap gap-3">
				<div className="relative min-w-0 flex-1">
					<Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
					<input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search by ID, number, title, program, or recipient" className="w-full rounded border border-slate-300 py-2 pl-9 pr-3 text-sm" />
				</div>
				<select value={status} onChange={(e) => setStatus(e.target.value)} className="rounded border border-slate-300 px-3 py-2 text-sm">
					{STATUSES.map((s) => (
						<option key={s} value={s}>{s || "All statuses"}</option>
					))}
				</select>
			</div>
			{error && <p className="mt-4 text-red-700">{error}</p>}
			<div className="mt-6 rounded-lg border border-slate-200 bg-white shadow-soft">
				{certificates.map((cert) => (
					<div key={cert.certificate_id} className="flex items-center justify-between border-b border-slate-100 px-5 py-4 last:border-b-0">
						<Link href={`/issuer/certificates/${cert.certificate_id}`} className="min-w-0">
							<span className="block font-semibold">{cert.certificate_id}</span>
							<span className="text-sm text-slate-500">{cert.recipient} · {cert.program}</span>
						</Link>
						<span className="ml-4 flex shrink-0 items-center gap-3">
							<StatusBadge status={cert.status} />
							{cert.status !== "REVOKED" && <button type="button" disabled={busy === cert.certificate_id} onClick={() => revoke(cert)} className="rounded border border-red-300 px-3 py-1 text-sm font-semibold text-red-700 disabled:opacity-60">Revoke</button>}
						</span>
					</div>
				))}
				{!error && certificates.length === 0 && <p className="p-5 text-slate-600">No certificates match this search.</p>}
			</div>
		</AppShell>
	);
}
