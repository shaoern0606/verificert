"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { API_URL } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    const form = new FormData(event.currentTarget);
    const response = await fetch(`${API_URL}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ full_name: form.get("full_name"), email: form.get("email"), password: form.get("password"), role: "RECIPIENT" }),
    });
    setLoading(false);
    if (!response.ok) { setError("This account could not be created."); return; }
    const token = await response.json();
    window.localStorage.setItem("verificert_token", token.access_token);
    window.localStorage.setItem("verificert_role", token.role);
    router.push("/recipient");
  }
  return (
    <AppShell>
      <form onSubmit={submit} className="mx-auto max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-soft">
        <h1 className="text-2xl font-bold">Register</h1>
        <input name="full_name" autoComplete="name" required className="mt-5 w-full rounded border border-slate-300 px-3 py-2" placeholder="Full name" />
        <input name="email" autoComplete="email" required className="mt-3 w-full rounded border border-slate-300 px-3 py-2" placeholder="Email" type="email" />
        <div className="relative"><input name="password" autoComplete="new-password" required minLength={8} className="mt-3 w-full rounded border border-slate-300 px-3 py-2 pr-11" placeholder="Password" type={showPassword ? "text" : "password"} /><button type="button" aria-label={showPassword ? "Hide password" : "Show password"} title={showPassword ? "Hide password" : "Show password"} onClick={() => setShowPassword((visible) => !visible)} className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-slate-500">{showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}</button></div>
        {error && <div className="mt-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
        <button disabled={loading} className="mt-5 w-full rounded bg-trust px-4 py-2 font-semibold text-white disabled:opacity-60">{loading ? "Creating account..." : "Create account"}</button>
      </form>
    </AppShell>
  );
}
