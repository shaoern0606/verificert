"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { API_URL } from "@/lib/api";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const [requestedRole, setRequestedRole] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  useEffect(() => setRequestedRole(new URLSearchParams(window.location.search).get("role")), []);

  return (
    <AppShell>
      <form
        className="mx-auto max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-soft"
        onSubmit={async (event) => {
          event.preventDefault();
          setError(null);
          setLoading(true);
          const form = new FormData(event.currentTarget);
          let response: Response;
          try {
            response = await fetch(`${API_URL}/api/auth/login`, {
              method: "POST",
              credentials: "include",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ email: form.get("email"), password: form.get("password") }),
            });
          } catch {
            setLoading(false);
            setError("The sign-in service is unavailable. Check that the API is running.");
            return;
          }
          setLoading(false);
          if (!response.ok) {
            setError(response.status === 401 ? "Email or password is incorrect." : "The sign-in service returned an error.");
            return;
          }
          const session = await response.json();
          window.localStorage.setItem("verificert_role", session.role);
          router.push(session.role === "ADMIN" ? "/admin" : session.role === "ISSUER" ? "/issuer" : "/recipient");
        }}
      >
        <h1 className="text-2xl font-bold">Sign in{requestedRole ? ` as ${requestedRole.toLowerCase()}` : ""}</h1>
        <label className="mt-5 block text-sm font-medium text-slate-700">Email<input name="email" autoComplete="email" className="mt-1 w-full rounded border border-slate-300 px-3 py-2" placeholder="Email" type="email" required /></label>
        <label className="mt-3 block text-sm font-medium text-slate-700">Password<div className="relative"><input name="password" autoComplete="current-password" className="mt-1 w-full rounded border border-slate-300 px-3 py-2 pr-11" placeholder="Password" type={showPassword ? "text" : "password"} required /><button type="button" aria-label={showPassword ? "Hide password" : "Show password"} title={showPassword ? "Hide password" : "Show password"} onClick={() => setShowPassword((visible) => !visible)} className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-slate-500">{showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}</button></div></label>
        {error && <div className="mt-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
        <button disabled={loading} className="mt-5 w-full rounded bg-trust px-4 py-2 font-semibold text-white disabled:opacity-60">
          {loading ? "Signing in..." : "Sign in"}
        </button>
        <p className="mt-4 text-center text-sm text-slate-600">
          Do not have an account? <Link href="/register" className="font-semibold text-trust">Register</Link>
        </p>
      </form>
    </AppShell>
  );
}
