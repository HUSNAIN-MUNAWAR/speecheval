import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/ui";
import { RunControlCenter } from "@/features/runs/run-control-center";
export default async function Page({ params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  return <AppShell><PageHeader eyebrow="Execution evidence" title="Run Control Center" description="Inspect lifecycle, immutable provenance, per-sample metrics, and durable worker events." action="Live runtime" /><RunControlCenter runId={runId} /></AppShell>;
}
