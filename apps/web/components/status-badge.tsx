import { clsx } from "clsx";

const colors: Record<string, string> = {
  VERIFIED: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  ACTIVE: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  EXPIRED: "bg-amber-50 text-amber-800 ring-amber-200",
  SUSPICIOUS: "bg-amber-50 text-amber-800 ring-amber-200",
  REVOKED: "bg-red-50 text-red-800 ring-red-200",
  INVALID: "bg-red-50 text-red-800 ring-red-200",
  PENDING: "bg-slate-100 text-slate-700 ring-slate-200",
  NOT_FOUND: "bg-slate-100 text-slate-700 ring-slate-200",
};

export function StatusBadge({ status }: { status: string }) {
  return <span className={clsx("inline-flex rounded px-2.5 py-1 text-xs font-semibold ring-1", colors[status] ?? colors.PENDING)}>{status.replace("_", " ")}</span>;
}
