import { AppShell } from "@/components/app-shell";
import { RegistryEmpty } from "@/components/registry-empty";
import { PageHeader } from "@/components/ui";
export default function Page() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Registry"
        title="Datasets"
        description="Versioned manifests, language coverage, rights metadata, and validation."
        action="Import dataset"
      />
      <RegistryEmpty kind="dataset" />
    </AppShell>
  );
}
