import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/ui";
import { BenchmarkLedger } from "@/features/evidence/evidence-panels";
export default function Page(){return <AppShell><PageHeader eyebrow="Research evidence" title="Benchmark ledger" description="Traceable benchmark cards, manifest hashes, and comparison integrity states." action="Evidence API"/><BenchmarkLedger/></AppShell>;}
