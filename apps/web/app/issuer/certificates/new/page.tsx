import { AppShell } from "@/components/app-shell";

export default function NewCertificatePage() {
  return (
    <AppShell>
      <section className="max-w-4xl rounded-lg border border-slate-200 bg-white p-6 shadow-soft">
        <h1 className="text-3xl font-bold text-ink">Issue Certificate</h1>
        <form className="mt-6 grid gap-4 md:grid-cols-2">
          {["Recipient name", "Recipient email", "Course/program name", "Certificate title", "Issue date", "Expiry date", "Certificate number", "Issuer ID"].map((label) => (
            <label key={label} className="text-sm font-medium text-slate-700">
              {label}
              <input className="mt-1 w-full rounded border border-slate-300 px-3 py-2" placeholder={label} />
            </label>
          ))}
          <label className="md:col-span-2 text-sm font-medium text-slate-700">
            Certificate PDF
            <input type="file" accept="application/pdf" className="mt-1 w-full rounded border border-slate-300 px-3 py-2" />
          </label>
          <button className="rounded bg-trust px-4 py-2 font-semibold text-white md:w-fit">Issue and Register</button>
        </form>
      </section>
    </AppShell>
  );
}
