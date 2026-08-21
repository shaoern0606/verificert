import { AppShell } from "@/components/app-shell";

export default function RegisterPage() {
  return (
    <AppShell>
      <form className="mx-auto max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-soft">
        <h1 className="text-2xl font-bold">Register</h1>
        <input className="mt-5 w-full rounded border border-slate-300 px-3 py-2" placeholder="Full name" />
        <input className="mt-3 w-full rounded border border-slate-300 px-3 py-2" placeholder="Email" />
        <input className="mt-3 w-full rounded border border-slate-300 px-3 py-2" placeholder="Password" type="password" />
        <button className="mt-5 w-full rounded bg-trust px-4 py-2 font-semibold text-white">Create account</button>
      </form>
    </AppShell>
  );
}
