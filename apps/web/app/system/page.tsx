import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/ui";
import { SystemHealth } from "@/features/evidence/evidence-panels";
export default function Page(){return <AppShell><PageHeader eyebrow="Operations" title="System health" description="Inspect API, database, worker, queue, storage, and metric-plugin readiness." action="Live health"/><SystemHealth/></AppShell>;}
