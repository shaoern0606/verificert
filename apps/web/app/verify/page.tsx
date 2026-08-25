"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import jsQR from "jsqr";
import { Camera, CircleX, Loader2, Search, Upload, X } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { VerificationResult } from "@/components/verification-result";
import { verifyByFile, VerificationResponse } from "@/lib/api";

function extractCertificateId(raw: string): string {
  const trimmed = raw.trim();
  try {
    const url = new URL(trimmed);
    const segments = url.pathname.split("/").filter(Boolean);
    return segments[segments.length - 1] || trimmed;
  } catch {
    return trimmed;
  }
}

export default function VerifyPage() {
  const router = useRouter();
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<VerificationResponse | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [scanning, setScanning] = useState(false);
  const [scanError, setScanError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const frameRef = useRef<number | null>(null);

  async function handleFile(file: File) {
    setUploading(true);
    setUploadError(null);
    setUploadResult(null);
    try {
      const result = await verifyByFile(file);
      setUploadResult(result);
    } catch {
      setUploadError("The upload could not be verified. Check that the API is running.");
    } finally {
      setUploading(false);
    }
  }

  function stopScanning() {
    if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
    frameRef.current = null;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setScanning(false);
  }

  async function startScanning() {
    setScanError(null);
    setUploadResult(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
      streamRef.current = stream;
      setScanning(true);
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      tick();
    } catch {
      setScanError("Camera access was denied or is unavailable. Try uploading the certificate file instead.");
      setScanning(false);
    }
  }

  function tick() {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState !== video.HAVE_ENOUGH_DATA) {
      frameRef.current = requestAnimationFrame(tick);
      return;
    }
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      frameRef.current = requestAnimationFrame(tick);
      return;
    }
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const code = jsQR(imageData.data, imageData.width, imageData.height);
    if (code && code.data) {
      const certificateId = extractCertificateId(code.data);
      stopScanning();
      router.push(`/verify/${encodeURIComponent(certificateId)}`);
      return;
    }
    frameRef.current = requestAnimationFrame(tick);
  }

  useEffect(() => () => stopScanning(), []);

  return (
    <AppShell>
      <section className="mx-auto max-w-3xl rounded-lg border border-slate-200 bg-white p-6 shadow-soft">
        <h1 className="text-3xl font-bold text-ink">Verify a Certificate</h1>
        <form
          className="mt-6 flex gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            const data = new FormData(event.currentTarget);
            const id = String(data.get("certificateId") ?? "").trim();
            if (id) router.push(`/verify/${encodeURIComponent(id)}`);
          }}
        >
          <input name="certificateId" className="min-w-0 flex-1 rounded border border-slate-300 px-3 py-2" placeholder="CERT-2026-000001" />
          <button className="inline-flex items-center gap-2 rounded bg-trust px-4 py-2 font-semibold text-white">
            <Search className="h-4 w-4" />
            Verify
          </button>
        </form>

        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(event) => {
              event.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(event) => {
              event.preventDefault();
              setDragging(false);
              const file = event.dataTransfer.files?.[0];
              if (file) handleFile(file);
            }}
            className={`flex flex-col items-center justify-center gap-2 rounded border-2 border-dashed p-6 text-center text-sm transition-colors ${
              dragging ? "border-trust bg-trust/5 text-trust" : "border-slate-300 text-slate-600 hover:border-slate-400"
            }`}
          >
            {uploading ? <Loader2 className="h-6 w-6 animate-spin" /> : <Upload className="h-6 w-6" />}
            <span className="font-semibold text-slate-800">{uploading ? "Checking document…" : "Drop a certificate file"}</span>
            <span>or click to browse — compares the exact file against the registered hash</span>
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf,image/jpeg,image/png,image/gif,image/webp"
              className="hidden"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) handleFile(file);
                event.target.value = "";
              }}
            />
          </button>

          <div className="flex flex-col items-center justify-center gap-2 rounded border-2 border-dashed border-slate-300 p-6 text-center text-sm text-slate-600">
            {scanning ? (
              <>
                <div className="relative w-full overflow-hidden rounded">
                  <video ref={videoRef} muted playsInline className="w-full rounded" />
                  <button type="button" onClick={stopScanning} aria-label="Stop scanning" className="absolute right-2 top-2 rounded-full bg-black/60 p-1 text-white">
                    <X className="h-4 w-4" />
                  </button>
                </div>
                <span>Point the camera at the certificate&apos;s QR code</span>
              </>
            ) : (
              <>
                <Camera className="h-6 w-6" />
                <span className="font-semibold text-slate-800">Scan a QR code</span>
                <button type="button" onClick={startScanning} className="mt-1 rounded bg-trust px-4 py-1.5 font-semibold text-white">
                  Open camera
                </button>
              </>
            )}
          </div>
        </div>
        <canvas ref={canvasRef} className="hidden" />

        {(uploadError || scanError) && (
          <div className="mt-4 flex items-center gap-2 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            <CircleX className="h-4 w-4 shrink-0" />
            {uploadError ?? scanError}
          </div>
        )}
      </section>

      {uploadResult && (
        <div className="mt-6">
          <VerificationResult result={uploadResult} />
        </div>
      )}
    </AppShell>
  );
}
