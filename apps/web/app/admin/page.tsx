"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BarChart, Bar, Cell, ResponsiveContainer, XAxis, YAxis, Tooltip, PieChart, Pie, Legend } from "recharts";
import { AppShell } from "@/components/app-shell";
import { getDashboard } from "@/lib/api";

const OUTCOME_COLORS: Record<string, string> = {
  VERIFIED: "#0f9d68",
  ACTIVE: "#0f9d68",
  INVALID: "#dc2626",
  REVOKED: "#dc2626",
  EXPIRED: "#d97706",
  SUSPICIOUS: "#d97706",
  PENDING: "#94a3b8",
  NOT_FOUND: "#64748b",
};

export default function AdminDashboard() {
  const [data, setData] = useState<{ cards: Record<string, number>; charts: Record<string, { name: string; value: number }[]> } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    getDashboard()
      .then((response) => {
        if (isMounted) setData(response);
      })
      .catch(() => {
        if (isMounted) setError("Unable to load dashboard data from the backend.");
      });

    return () => {
      isMounted = false;
    };
  }, []);

  if (error) {
    return (
      <AppShell>
        <h1 className="text-3xl font-bold text-ink">Admin Dashboard</h1>
        <div className="mt-6 rounded border border-red-200 bg-red-50 p-4 text-red-700">{error}</div>
      </AppShell>
    );
  }

  if (!data) {
    return (
      <AppShell>
        <h1 className="text-3xl font-bold text-ink">Admin Dashboard</h1>
        <div className="mt-6 rounded border border-slate-200 bg-white p-5 text-slate-600">Loading backend data…</div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <h1 className="text-3xl font-bold text-ink">Admin Dashboard</h1>
      <div className="mt-6 grid gap-4 md:grid-cols-3">
        {Object.entries(data.cards).map(([key, value]) => (
          <div key={key} className="rounded-lg border border-slate-200 bg-white p-5 shadow-soft">
            <p className="text-sm font-medium text-slate-500">{key.replaceAll("_", " ")}</p>
            <p className="mt-2 text-3xl font-bold text-ink">{value}</p>
          </div>
        ))}
      </div>
      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <div className="h-80 rounded-lg border border-slate-200 bg-white p-5 shadow-soft">
          <p className="mb-2 text-sm font-semibold text-slate-700">Certificates by status</p>
          <ResponsiveContainer width="100%" height="90%">
            <BarChart data={data.charts.certificates_by_status ?? []}>
              <XAxis dataKey="name" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" fill="#13795b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="h-80 rounded-lg border border-slate-200 bg-white p-5 shadow-soft">
          <p className="mb-2 text-sm font-semibold text-slate-700">Verification outcomes</p>
          <ResponsiveContainer width="100%" height="90%">
            <PieChart>
              <Tooltip />
              <Legend />
              <Pie data={data.charts.verification_outcomes ?? []} dataKey="value" nameKey="name" innerRadius={50} outerRadius={90}>
                {(data.charts.verification_outcomes ?? []).map((entry) => (
                  <Cell key={entry.name} fill={OUTCOME_COLORS[entry.name] ?? "#94a3b8"} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="mt-6 flex flex-wrap gap-3">
        <Link href="/admin/issuers" className="inline-flex rounded bg-trust px-4 py-2 font-semibold text-white">Issuer Management</Link>
        <Link href="/admin/certificates" className="inline-flex rounded border border-slate-300 bg-white px-4 py-2 font-semibold text-slate-700">View Issued Certificates</Link>
        <Link href="/admin/verifications" className="inline-flex rounded border border-slate-300 bg-white px-4 py-2 font-semibold text-slate-700">Verification Attempts</Link>
        <Link href="/admin/audit-logs" className="inline-flex rounded border border-slate-300 bg-white px-4 py-2 font-semibold text-slate-700">Audit Logs</Link>
        <Link href="/admin/api-keys" className="inline-flex rounded border border-slate-300 bg-white px-4 py-2 font-semibold text-slate-700">API Keys</Link>
      </div>
    </AppShell>
  );
}
