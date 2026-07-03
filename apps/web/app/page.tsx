import { AppShell } from "@/components/app-shell";
import { OverviewDashboard } from "@/features/overview/overview-dashboard";
export default function Page() {
  return (
    <AppShell>
      <OverviewDashboard />
    </AppShell>
  );
}
