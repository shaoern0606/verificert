import { AppShell } from "@/components/app-shell";
export default async function Page({ params }: { params: Promise<{ id: string }> }) { const { id } = await params; return <AppShell><h1 className="text-3xl font-bold">{id}</h1></AppShell>; }
