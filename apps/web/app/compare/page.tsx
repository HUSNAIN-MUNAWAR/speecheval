import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/ui";
import { ComparePreview } from "@/features/compare/compare-preview";
export default function Page() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Analysis"
        title="Compare runs"
        description="Inspect tradeoffs by metric, language, tags, and individual audio samples."
        action="Select runs"
      />
      <ComparePreview />
    </AppShell>
  );
}
