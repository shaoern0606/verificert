"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { CertificateListItem, getCertificates } from "@/lib/api";

const STATUSES = ["", "ACTIVE", "EXPIRED", "REVOKED", "PENDING", "FAILED"];

export default function Page() {
	const [certificates, setCertificates] = useState<CertificateListItem[]>([]);
	const [error, setError] = useState<string | null>(null);
	const [q, setQ] = useState("");
	const [status, setStatus] = useState("");

	useEffect(() => {
		const handle = setTimeout(() => {
			getCertificates({ q: q || undefined, status: status || undefined }).then(setCertificates).catch(() => setError("Unable to load certificates from the backend."));
		}, 250);
		return () => clearTimeout(handle);
	}, [q, status]);

	return (
		<AppShell>
			<h1 className="text-3xl font-bold">Certificates</h1>
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
				{certificates.map((certificate) => (
					<Link key={certificate.certificate_id} href={`/verify/${certificate.certificate_id}`} className="flex items-center justify-between border-b border-slate-100 px-5 py-4 last:border-b-0">
						<span>
							<span className="block font-semibold">{certificate.certificate_id}</span>
							<span className="text-sm text-slate-500">{certificate.recipient} · {certificate.issuer}</span>
						</span>
						<span className="text-sm font-semibold">{certificate.status}</span>
					</Link>
				))}
				{!error && certificates.length === 0 && <p className="p-5 text-slate-600">No certificates match this search.</p>}
			</div>
		</AppShell>
	);
}
