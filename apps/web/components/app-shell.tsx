import Link from "next/link";
import { ShieldCheck } from "lucide-react";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-panel text-ink">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6">
          <Link href="/" className="flex items-center gap-2 font-bold">
            <ShieldCheck className="h-6 w-6 text-trust" />
            VERIFICERT
          </Link>
          <nav className="flex gap-4 text-sm font-medium text-slate-700">
            <Link href="/verify">Verify</Link>
            <Link href="/issuer">Issuer</Link>
            <Link href="/admin">Admin</Link>
            <Link href="/recipient">Recipient</Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6">{children}</main>
    </div>
  );
}
