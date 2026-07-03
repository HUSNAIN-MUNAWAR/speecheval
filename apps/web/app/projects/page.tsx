import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/ui";
import { ProjectTable } from "@/features/projects/project-table";
export default function Page() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Workspace"
        title="Projects"
        description="Benchmark workspaces with datasets, models, baselines, and regression history."
        action="Create project"
      />
      <ProjectTable />
    </AppShell>
  );
}
