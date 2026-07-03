import { AppShell } from "@/components/app-shell";
import { RegistryEmpty } from "@/components/registry-empty";
import { PageHeader } from "@/components/ui";
export default function Page() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Registry"
        title="Models"
        description="Track immutable model versions, code provenance, images, and capabilities."
        action="Register model"
      />
      <RegistryEmpty kind="model" />
    </AppShell>
  );
}
