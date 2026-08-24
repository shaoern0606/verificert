"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BarChart, Bar, ResponsiveContainer, XAxis, YAxis, Tooltip } from "recharts";
import { AppShell } from "@/components/app-shell";
import { getDashboard } from "@/lib/api";

export default function AdminDashboard() {
  const [data, setData] = useState<{ cards: Record<string, number>; charts: Record<string, { name: string; value: number }[]> } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const token = window.localStorage.getItem("verificert_token");
    if (!token) {
      setError("Sign in as an admin to load dashboard data.");
      return () => {
        isMounted = false;
      };
    }

    getDashboard(token)
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
      <div className="mt-6 h-80 rounded-lg border border-slate-200 bg-white p-5 shadow-soft">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data.charts.certificates_by_status ?? []}>
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#13795b" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-6 flex flex-wrap gap-3">
        <Link href="/admin/issuers" className="inline-flex rounded bg-trust px-4 py-2 font-semibold text-white">Issuer Management</Link>
        <Link href="/admin/certificates" className="inline-flex rounded border border-slate-300 bg-white px-4 py-2 font-semibold text-slate-700">View Issued Certificates</Link>
      </div>
    </AppShell>
  );
}
