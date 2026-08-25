"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { CurrentUser, getCurrentUser, logout } from "@/lib/api";

const roleDestinations = { ISSUER: "/issuer", ADMIN: "/admin", RECIPIENT: "/recipient" } as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<CurrentUser | null>(null);
  useEffect(() => {
    getCurrentUser().then(setUser).catch(() => {
      setUser(null);
      window.localStorage.removeItem("verificert_role");
    });
  }, [pathname]);
  function openRole(role: keyof typeof roleDestinations) {
    if (user?.role === role) return router.push(roleDestinations[role]);
    if (user && user.role in roleDestinations) return router.push(roleDestinations[user.role as keyof typeof roleDestinations]);
    window.location.assign(`/login?role=${role}`);
  }
  async function signOut() {
    await logout();
    window.localStorage.removeItem("verificert_role");
    setUser(null);
    router.push("/login");
  }
  return (
    <div className="min-h-screen bg-panel text-ink">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6">
          <Link href="/" className="flex items-center gap-2 font-bold">
            <ShieldCheck className="h-6 w-6 text-trust" />
            VERIFICERT
          </Link>
          <nav className="flex items-center gap-4 text-sm font-medium text-slate-700">
            <Link href="/verify" className="inline-flex h-6 items-center px-0 font-[inherit] leading-6">Verify</Link>
            <Link href="/issuers" className="inline-flex h-6 items-center px-0 font-[inherit] leading-6">Issuers</Link>
            <button type="button" onClick={() => openRole("ISSUER")} className="inline-flex h-6 items-center px-0 font-[inherit] leading-6">Issuer</button>
            <button type="button" onClick={() => openRole("ADMIN")} className="inline-flex h-6 items-center px-0 font-[inherit] leading-6">Admin</button>
            <button type="button" onClick={() => openRole("RECIPIENT")} className="inline-flex h-6 items-center px-0 font-[inherit] leading-6">Recipient</button>
            {user ? <span className="flex items-center gap-2 border-l border-slate-200 pl-4"><span className="text-right"><span className="block font-semibold text-ink">{user.full_name}</span><span className="block text-xs text-slate-500">{user.email} · {user.role}</span></span><button type="button" onClick={signOut} className="text-trust">Sign out</button></span> : <Link href="/login" className="text-trust">Sign in</Link>}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6">{children}</main>
    </div>
  );
}
