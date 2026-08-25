"use client";

import { useState } from "react";
import { AlertTriangle, CheckCircle2, CircleX, Code2, FileCheck2, Linkedin, Link as LinkIcon, ShieldCheck } from "lucide-react";
import { QRCodeSVG } from "qrcode.react";
import { StatusBadge } from "./status-badge";
import { API_URL, type VerificationResponse } from "@/lib/api";

const iconMap = {
  VERIFIED: <CheckCircle2 className="h-12 w-12 text-emerald-700" />,
  INVALID: <CircleX className="h-12 w-12 text-red-700" />,
  REVOKED: <CircleX className="h-12 w-12 text-red-700" />,
  EXPIRED: <AlertTriangle className="h-12 w-12 text-amber-700" />,
  SUSPICIOUS: <AlertTriangle className="h-12 w-12 text-amber-700" />,
  NOT_FOUND: <CircleX className="h-12 w-12 text-slate-600" />,
  PENDING: <AlertTriangle className="h-12 w-12 text-slate-600" />,
};

export function VerificationResult({ result }: { result: VerificationResponse }) {
  const cert = result.certificate;
  return (
    <section className="grid gap-6 lg:grid-cols-[1.4fr_0.8fr]">
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-soft">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-center gap-4">
            {iconMap[result.status]}
            <div>
              <p className="text-sm font-semibold text-slate-500">VERIFICERT</p>
              <h1 className="mt-1 text-3xl font-bold text-ink">{result.status === "VERIFIED" ? "Certificate Verified" : "Verification Attention Required"}</h1>
            </div>
          </div>
          <StatusBadge status={result.status} />
        </div>
        <p className="mt-5 max-w-3xl text-base text-slate-700">{result.decisive_reason}</p>
        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          {Object.entries(result.checks).map(([name, ok]) => (
            <div key={name} className="flex items-center gap-3 rounded border border-slate-200 bg-panel px-3 py-3">
              {ok ? <CheckCircle2 className="h-5 w-5 text-emerald-700" /> : <CircleX className="h-5 w-5 text-red-700" />}
              <span className="text-sm font-medium text-slate-800">{name.replaceAll("_", " ")}</span>
            </div>
          ))}
        </div>
        {cert && (
          <dl className="mt-8 grid gap-4 border-t border-slate-200 pt-6 sm:grid-cols-2">
            <Info label="Certificate ID" value={cert.certificate_id} />
            <Info label="Recipient" value={cert.recipient} />
            <Info label="Program" value={cert.program} />
            <Info label="Issuer" value={cert.issuer} />
            <Info label="Issued" value={formatDate(cert.issued)} />
            <Info label="Certificate Status" value={cert.status} />
          </dl>
        )}
        {cert && result.status === "VERIFIED" && (
          <SharePanel
            certificateId={cert.certificate_id}
            verificationUrl={cert.verification_url}
            program={cert.program}
            issuer={cert.issuer}
            issued={cert.issued}
          />
        )}
        {cert && result.status !== "VERIFIED" && (
          <p className="mt-8 border-t border-slate-200 pt-6 text-sm text-slate-500">
            Sharing and LinkedIn options are disabled because this certificate&apos;s current status is {result.status.toLowerCase()}, not verified.
          </p>
        )}
      </div>
      <aside className="rounded-lg border border-slate-200 bg-white p-5 shadow-soft">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
          <ShieldCheck className="h-4 w-4" />
          Trust Details
        </div>
        {cert ? (
          <>
            <div className="mt-5 flex justify-center rounded border border-slate-200 p-4">
              <QRCodeSVG value={cert.verification_url} size={156} />
            </div>
            <div className="mt-5 space-y-3 text-sm">
              <Info label="Document Hash" value={`${cert.document_hash.slice(0, 18)}...`} />
              <Info label="Transaction" value={cert.transaction_hash ? `${cert.transaction_hash.slice(0, 18)}...` : "Pending"} />
              <Info label="Risk" value={`${result.ai?.risk_level ?? "UNKNOWN"} (${result.ai?.risk_score ?? 0}/100)`} />
            </div>
            <details className="mt-5 rounded border border-slate-200 p-3 text-sm">
              <summary className="cursor-pointer font-semibold text-slate-700">Technical Details</summary>
              <pre className="mt-3 max-h-60 overflow-auto whitespace-pre-wrap text-xs text-slate-600">{JSON.stringify(result.technical_details, null, 2)}</pre>
            </details>
          </>
        ) : (
          <div className="mt-5 flex items-center gap-3 rounded border border-slate-200 p-4 text-sm text-slate-600">
            <FileCheck2 className="h-5 w-5" />
            No public credential record is available.
          </div>
        )}
      </aside>
    </section>
  );
}

function SharePanel({
  certificateId,
  verificationUrl,
  program,
  issuer,
  issued,
}: {
  certificateId: string;
  verificationUrl: string;
  program: string;
  issuer: string;
  issued: string;
}) {
  const [copied, setCopied] = useState<"link" | "html" | "markdown" | null>(null);
  const badgeUrl = `${API_URL}/api/certificates/${encodeURIComponent(certificateId)}/badge.svg`;
  const htmlEmbed = `<a href="${verificationUrl}"><img src="${badgeUrl}" alt="VERIFICERT credential badge" /></a>`;
  const markdownEmbed = `[![VERIFICERT credential badge](${badgeUrl})](${verificationUrl})`;

  const issuedDate = new Date(issued);
  const linkedInAddUrl = `https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME&name=${encodeURIComponent(program)}&organizationName=${encodeURIComponent(issuer)}&issueYear=${issuedDate.getFullYear()}&issueMonth=${issuedDate.getMonth() + 1}&certUrl=${encodeURIComponent(verificationUrl)}&certId=${encodeURIComponent(certificateId)}`;

  async function copy(text: string, kind: "link" | "html" | "markdown") {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(kind);
      setTimeout(() => setCopied(null), 2000);
    } catch {
      // clipboard access can be denied by the browser; the text fields remain selectable manually
    }
  }

  return (
    <div className="mt-8 border-t border-slate-200 pt-6">
      <p className="text-sm font-semibold text-slate-700">Share this credential</p>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <a
          href={linkedInAddUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded bg-[#0a66c2] px-3 py-1.5 text-sm font-semibold text-white"
        >
          <Linkedin className="h-4 w-4" />
          Add to LinkedIn profile
        </a>
        <button type="button" onClick={() => copy(verificationUrl, "link")} className="inline-flex items-center gap-2 rounded border border-slate-300 px-3 py-1.5 text-sm font-semibold text-slate-700">
          <LinkIcon className="h-4 w-4" />
          {copied === "link" ? "Copied!" : "Copy link"}
        </button>
        <button type="button" onClick={() => copy(htmlEmbed, "html")} className="inline-flex items-center gap-2 rounded border border-slate-300 px-3 py-1.5 text-sm font-semibold text-slate-700">
          <Code2 className="h-4 w-4" />
          {copied === "html" ? "Copied!" : "Copy HTML embed"}
        </button>
        <button type="button" onClick={() => copy(markdownEmbed, "markdown")} className="inline-flex items-center gap-2 rounded border border-slate-300 px-3 py-1.5 text-sm font-semibold text-slate-700">
          <Code2 className="h-4 w-4" />
          {copied === "markdown" ? "Copied!" : "Copy Markdown embed"}
        </button>
      </div>
      <div className="mt-3 flex items-center gap-3 rounded border border-dashed border-slate-300 bg-panel p-3">
        <img src={badgeUrl} alt="VERIFICERT credential badge" />
        <span className="text-xs text-slate-500">Live badge — embeddable on a resume, portfolio, GitHub README, or LinkedIn.</span>
      </div>
    </div>
  );
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="mt-1 break-words text-sm font-semibold text-slate-900">{value}</dd>
    </div>
  );
}
