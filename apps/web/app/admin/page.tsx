"use client";

import { BarChart, Bar, ResponsiveContainer, XAxis, YAxis, Tooltip } from "recharts";
import { AppShell } from "@/components/app-shell";

const data = {
  cards: { total_certificates: 30, active: 20, expired: 5, revoked: 5, registered_issuers: 5, verification_attempts: 12 },
  charts: { certificates_by_status: [{ name: "ACTIVE", value: 20 }, { name: "EXPIRED", value: 5 }, { name: "REVOKED", value: 5 }] },
};

export default function AdminDashboard() {
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
    </AppShell>
  );
}
