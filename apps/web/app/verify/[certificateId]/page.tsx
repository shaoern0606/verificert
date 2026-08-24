import { AppShell } from "@/components/app-shell";
import { VerificationResult } from "@/components/verification-result";
import { verifyCertificate } from "@/lib/api";

export default async function VerifyCertificatePage({ params }: { params: Promise<{ certificateId: string }> }) {
  const { certificateId } = await params;
  const result = await verifyCertificate(certificateId);
  return (
    <AppShell>
      <VerificationResult result={result} />
    </AppShell>
  );
}
