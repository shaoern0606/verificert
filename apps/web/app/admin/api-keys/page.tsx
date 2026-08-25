"use client";

import { FormEvent, useEffect, useState } from "react";
import { Copy, KeyRound } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { ApiKeySummary, createApiKey, listApiKeys, revokeApiKey } from "@/lib/api";

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKeySummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [newKey, setNewKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  function load() {
    listApiKeys().then(setKeys).catch(() => setError("Unable to load API keys from the backend."));
  }

  useEffect(load, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const label = String(form.get("label") ?? "").trim();
    if (!label) return;
    try {
      const created = await createApiKey(label);
      setNewKey(created.key);
      event.currentTarget.reset();
      load();
    } catch {
      setError("The API key could not be created.");
    }
  }

  async function revoke(id: string) {
    if (!window.confirm("Revoke this API key? Any integration using it will stop working immediately.")) return;
    setBusy(id);
    try {
      await revokeApiKey(id);
      load();
    } catch {
      setError("The API key could not be revoked.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <AppShell>
      <h1 className="text-3xl font-bold">API Keys</h1>
      <p className="mt-2 text-slate-600">Issue keys for programmatic access to <code>/api/verify</code>. Keys attribute audit-log entries to the integration instead of &quot;public&quot; and let you revoke access without changing any user&apos;s password.</p>
      {error && <p className="mt-4 text-red-700">{error}</p>}

      {newKey && (
        <div className="mt-6 rounded-lg border border-amber-300 bg-amber-50 p-4">
          <p className="text-sm font-semibold text-amber-900">Copy this key now — it will not be shown again.</p>
          <div className="mt-2 flex items-center gap-2">
            <code className="flex-1 overflow-x-auto rounded bg-white px-3 py-2 text-sm">{newKey}</code>
            <button
              type="button"
              onClick={async () => { await navigator.clipboard.writeText(newKey); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
              className="inline-flex items-center gap-1 rounded border border-amber-400 px-3 py-2 text-sm font-semibold text-amber-900"
            >
              <Copy className="h-4 w-4" />
              {copied ? "Copied" : "Copy"}
            </button>
          </div>
          <p className="mt-2 text-xs text-amber-800">Send it as an <code>X-API-Key</code> header when calling the verify endpoints.</p>
        </div>
      )}

      <form onSubmit={submit} className="mt-6 flex max-w-md gap-3">
        <input name="label" required placeholder='Label, e.g. "Acme HR portal"' className="min-w-0 flex-1 rounded border border-slate-300 px-3 py-2 text-sm" />
        <button className="inline-flex items-center gap-2 rounded bg-trust px-4 py-2 text-sm font-semibold text-white">
          <KeyRound className="h-4 w-4" />
          Create key
        </button>
      </form>

      <div className="mt-6 overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-soft">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-slate-500">
              <th className="px-4 py-3">Label</th>
              <th className="px-4 py-3">Key prefix</th>
              <th className="px-4 py-3">Created by</th>
              <th className="px-4 py-3">Last used</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {keys.map((key) => (
              <tr key={key.id} className="border-b border-slate-100">
                <td className="px-4 py-3 font-semibold">{key.label}</td>
                <td className="px-4 py-3 font-mono text-xs">{key.prefix}…</td>
                <td className="px-4 py-3">{key.created_by}</td>
                <td className="px-4 py-3">{key.last_used_at ? new Date(key.last_used_at).toLocaleString() : "Never"}</td>
                <td className="px-4 py-3">{key.revoked ? <span className="text-red-700">Revoked</span> : <span className="text-emerald-700">Active</span>}</td>
                <td className="px-4 py-3">
                  {!key.revoked && (
                    <button type="button" disabled={busy === key.id} onClick={() => revoke(key.id)} className="rounded border border-red-300 px-3 py-1 text-xs font-semibold text-red-700 disabled:opacity-60">
                      Revoke
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!error && keys.length === 0 && <p className="p-5 text-slate-600">No API keys have been created.</p>}
      </div>
    </AppShell>
  );
}
