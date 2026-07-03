import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/ui";
import { ListeningLab } from "@/features/evidence/evidence-panels";
export default function Page(){return <AppShell><PageHeader eyebrow="Human evaluation" title="Listening Lab" description="A/B, ABX, and rating-study infrastructure with randomized tasks and explicit limitations." action="Study API"/><ListeningLab/></AppShell>;}
