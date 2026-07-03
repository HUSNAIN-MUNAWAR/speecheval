import { ArrowUpRight, CheckCircle2, Filter, Search } from "lucide-react";
import { StatusBadge } from "@/components/ui";
const projects = [
  {
    name: "Multilingual Narration Regression",
    description: "Synthetic fixture workspace",
    tags: ["Demo Data", "Multilingual"],
    runs: 3,
    health: "warning" as const,
    updated: "12m ago",
  },
  {
    name: "Voice Cloning Quality Audit",
    description: "Template available after dataset import",
    tags: ["Template"],
    runs: 0,
    health: "draft" as const,
    updated: "Never",
  },
];
export function ProjectTable() {
  return (
    <section className="panel overflow-hidden">
      <div className="flex flex-col gap-3 border-b border-line p-4 sm:flex-row">
        <label className="flex min-w-0 flex-1 items-center gap-2 rounded-xl border border-line bg-surface px-3 py-2 text-sm text-muted">
          <Search size={16} />
          <input
            aria-label="Search projects"
            placeholder="Search projects · Phase 1 preview"
            disabled
            className="w-full cursor-not-allowed bg-transparent outline-none"
          />
        </label>
        <button
          disabled
          className="inline-flex cursor-not-allowed items-center gap-2 rounded-xl border border-line px-3 py-2 text-sm text-muted"
        >
          <Filter size={15} />
          Filters
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px] text-left">
          <thead className="border-b border-line bg-surface/50 text-[11px] uppercase tracking-[.13em] text-muted">
            <tr>
              <th className="px-5 py-3">Project</th>
              <th className="px-5 py-3">Tags</th>
              <th className="px-5 py-3">Runs</th>
              <th className="px-5 py-3">Health</th>
              <th className="px-5 py-3">Last activity</th>
              <th className="px-5 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {projects.map((p) => (
              <tr key={p.name} className="hover:bg-white/[.025]">
                <td className="px-5 py-4">
                  <p className="font-medium">{p.name}</p>
                  <p className="mt-1 text-xs text-muted">{p.description}</p>
                </td>
                <td className="px-5 py-4">
                  <div className="flex gap-1.5">
                    {p.tags.map((t) => (
                      <span
                        key={t}
                        className="rounded-md border border-line bg-surface px-2 py-1 text-[10px] text-muted"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="mono px-5 py-4 text-sm">{p.runs}</td>
                <td className="px-5 py-4">
                  <StatusBadge status={p.health} />
                </td>
                <td className="mono px-5 py-4 text-xs text-muted">
                  {p.updated}
                </td>
                <td className="px-5 py-4">
                  <ArrowUpRight size={16} className="text-muted" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center gap-2 border-t border-line bg-surface/30 p-3 text-xs text-muted">
        <CheckCircle2 size={14} className="text-emerald-300" />
        Demo project metadata is seeded through the backend.
      </div>
    </section>
  );
}
