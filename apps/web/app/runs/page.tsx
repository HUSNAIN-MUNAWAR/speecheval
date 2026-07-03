import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/ui";
import { RunsTable } from "@/features/runs/runs-table";
export default function Page() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Execution"
        title="Evaluation runs"
        description="Trace reproducible quality and performance checks across model versions."
        action="Start evaluation"
      />
      <RunsTable />
    </AppShell>
  );
}
