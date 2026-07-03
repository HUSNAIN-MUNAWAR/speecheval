"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { FileDown, Play, Search } from "lucide-react";
import { platformApi, type Run } from "@/lib/api";
import { StatusBadge } from "@/components/ui";

function tone(run: Run): "pass" | "warning" | "fail" | "draft" {
  if (run.regression_decision === "fail" || run.status === "FAILED") return "fail";
  if (run.regression_decision === "warning" || run.status === "PARTIAL") return "warning";
  if (run.status === "COMPLETED") return "pass";
  return "draft";
}

export function RunsTable() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { platformApi.runs().then((x) => setRuns(x.items)).catch((x: Error) => setError(x.message)); }, []);
  const visible = runs.filter((run) => run.name.toLowerCase().includes(query.toLowerCase()));
  return <section className="panel overflow-hidden">
    <div className="flex flex-col gap-3 border-b border-line p-4 sm:flex-row">
      <label className="flex min-w-0 flex-1 items-center gap-2 rounded-xl border border-line bg-surface px-3 py-2 text-sm text-muted"><Search size={16} /><input aria-label="Search runs" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search real run records" className="w-full bg-transparent outline-none" /></label>
      <span className="inline-flex items-center gap-2 rounded-xl border border-line px-3 py-2 text-xs text-muted"><FileDown size={15} />Export from Run Control Center</span>
    </div>
    {error ? <p className="p-5 text-sm text-rose-200">API unavailable: {error}</p> : <div className="overflow-x-auto"><table className="w-full min-w-[860px] text-left"><thead className="border-b border-line bg-surface/50 text-[11px] uppercase tracking-[.13em] text-muted"><tr><th className="px-5 py-3">Run</th><th className="px-5 py-3">Stage</th><th className="px-5 py-3">Coverage</th><th className="px-5 py-3">Profile</th><th className="px-5 py-3">Decision</th><th className="px-5 py-3">Open</th></tr></thead><tbody className="divide-y divide-line">{visible.map((run) => <tr key={run.id} className="hover:bg-white/[.025]"><td className="px-5 py-4"><p className="font-medium">{run.name}</p><p className="mono mt-1 text-[10px] text-muted">{run.id.slice(0, 8)} · {run.manifest_hash ? "manifest frozen" : "draft manifest"}</p></td><td className="mono px-5 py-4 text-xs text-muted">{run.current_stage ?? run.status}</td><td className="mono px-5 py-4 text-xs text-muted">{run.processed_items} / {run.total_items}</td><td className="mono px-5 py-4 text-xs text-muted">{run.execution_profile_id}</td><td className="px-5 py-4"><StatusBadge status={tone(run)} /></td><td className="px-5 py-4"><Link href={`/runs/${run.id}`} className="inline-flex items-center gap-1 rounded-lg border border-line px-2 py-1.5 text-xs hover:bg-white/[.05]"><Play size={12} />Control center</Link></td></tr>)}</tbody></table></div>}
  </section>;
}
