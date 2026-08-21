import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VERIFICERT",
  description: "Verifiable digital credentials with blockchain-backed integrity and AI-assisted fraud analysis.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
