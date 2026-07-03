"use client";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, CircleStop, FileJson, Play, ShieldCheck, Waves } from "lucide-react";
import { platformApi, type Run } from "@/lib/api";
import { StatusBadge } from "@/components/ui";

function badge(status: string): "pass" | "warning" | "fail" | "draft" {
  if (status === "COMPLETED") return "pass";
  if (status === "PARTIAL") return "warning";
  if (status === "FAILED") return "fail";
  return "draft";
}

export function RunControlCenter({ runId }: { runId: string }) {
  const [run, setRun] = useState<Run | null>(null);
  const [samples, setSamples] = useState<Awaited<ReturnType<typeof platformApi.samples>>["items"]>([]);
  const [events, setEvents] = useState<Awaited<ReturnType<typeof platformApi.events>>["items"]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const load = useCallback(async () => {
    try {
      const [nextRun, nextSamples, nextEvents] = await Promise.all([
        platformApi.run(runId),
        platformApi.samples(runId),
        platformApi.events(runId),
      ]);
      setRun(nextRun);
      setSamples(nextSamples.items);
      setEvents(nextEvents.items);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load run evidence");
    }
  }, [runId]);
  useEffect(() => {
    void load();
    const id = setInterval(() => {
      void load();
    }, 1800);
    return () => clearInterval(id);
  }, [load]);
  const failures = useMemo(() => samples.filter((sample) => sample.status !== "COMPLETED").length, [samples]);
  if (error) return <div className="panel p-6 text-rose-200">Control Center could not load: {error}</div>;
  if (!run) return <div className="panel p-6 text-muted">Loading persistent run evidence…</div>;
  const start = async () => { setBusy(true); try { await platformApi.enqueue(run.id); await load(); } catch (err) { setError(err instanceof Error ? err.message : "Unable to enqueue"); } finally { setBusy(false); } };
  const cancel = async () => { setBusy(true); try { await platformApi.cancel(run.id); await load(); } catch (err) { setError(err instanceof Error ? err.message : "Unable to cancel"); } finally { setBusy(false); } };
  return <div className="space-y-5">
    <section className="panel overflow-hidden"><div className="border-b border-line p-5"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="eyebrow">Run Control Center</p><h2 className="mt-2 text-xl font-semibold">{run.name}</h2><p className="mono mt-2 text-xs text-muted">{run.id} · {run.execution_profile_id}</p></div><div className="flex items-center gap-2"><StatusBadge status={badge(run.status)} />{run.status === "DRAFT" && <button disabled={busy} onClick={start} className="inline-flex items-center gap-2 rounded-xl bg-accent px-3 py-2 text-sm font-semibold text-slate-950"><Play size={15} />Enqueue</button>}{["QUEUED", "VALIDATING", "PREPARING", "RUNNING"].includes(run.status) && <button disabled={busy} onClick={cancel} className="inline-flex items-center gap-2 rounded-xl border border-danger/40 px-3 py-2 text-sm text-rose-200"><CircleStop size={15} />Cancel</button>}</div></div></div>
      <div className="grid gap-px bg-line md:grid-cols-4"><div className="bg-panel p-4"><p className="eyebrow">Progress</p><p className="mono mt-2 text-2xl">{run.processed_items}/{run.total_items}</p></div><div className="bg-panel p-4"><p className="eyebrow">Stage</p><p className="mono mt-2 text-sm">{run.current_stage ?? run.status}</p></div><div className="bg-panel p-4"><p className="eyebrow">Failures / partial</p><p className="mono mt-2 text-2xl">{failures}</p></div><div className="bg-panel p-4"><p className="eyebrow">Manifest</p><p className="mono mt-2 truncate text-xs">{run.manifest_hash ?? "not frozen"}</p></div></div>
    </section>
    <section className="grid gap-5 xl:grid-cols-[1.2fr_.8fr]"><article className="panel overflow-hidden"><div className="flex items-center justify-between border-b border-line p-4"><div><p className="eyebrow">Sample triage</p><p className="mt-1 text-sm text-muted">Real persisted sample results, metric availability, and warnings.</p></div><Waves className="text-accent" size={18} /></div><div className="max-h-[420px] overflow-auto"><table className="w-full text-left text-sm"><thead className="sticky top-0 bg-surface text-[10px] uppercase tracking-[.12em] text-muted"><tr><th className="px-4 py-3">Sample</th><th className="px-4 py-3">Language</th><th className="px-4 py-3">WER</th><th className="px-4 py-3">Clipping</th><th className="px-4 py-3">State</th></tr></thead><tbody className="divide-y divide-line">{samples.map((sample) => { const metric=(id: string) => sample.metrics.find((m) => m.id === id); return <tr key={sample.id}><td className="px-4 py-3"><p className="mono text-xs">{sample.sample_key}</p><p className="mt-1 max-w-sm truncate text-xs text-muted">{sample.expected_text}</p></td><td className="mono px-4 py-3 text-xs">{sample.language}</td><td className="mono px-4 py-3 text-xs">{metric("wer")?.value?.toFixed(3) ?? metric("wer")?.status ?? "—"}</td><td className="mono px-4 py-3 text-xs">{metric("clipping")?.value?.toFixed(4) ?? "—"}</td><td className="px-4 py-3"><StatusBadge status={sample.status === "COMPLETED" ? "pass" : sample.status === "PARTIAL" ? "warning" : "draft"} /></td></tr>; })}</tbody></table></div></article>
    <article className="panel p-4"><div className="flex items-center gap-2"><Activity size={17} className="text-accent"/><div><p className="eyebrow">Live execution log</p><p className="text-xs text-muted">Ordered, durable event stream</p></div></div><div className="mono mt-4 max-h-[360px] space-y-3 overflow-auto text-[11px] text-muted">{events.map((event) => <div key={event.sequence} className="border-l border-line pl-3"><p className="text-ink">{event.sequence.toString().padStart(3,"0")} · {event.type}</p><p>{event.stage ?? "-"} · {event.message}</p></div>)}{events.length === 0 && <p>No events recorded yet.</p>}</div><div className="mt-4 border-t border-line pt-3"><button className="inline-flex items-center gap-2 text-xs text-muted hover:text-ink" onClick={() => navigator.clipboard.writeText(run.manifest_hash ?? "")}><FileJson size={14}/>Copy manifest hash</button><p className="mt-3 flex items-start gap-2 text-xs leading-5 text-muted"><ShieldCheck size={14} className="mt-0.5 text-success"/>Signal metrics are CPU-derived. WER/CER may be marked mock/manual when no ASR adapter is configured.</p></div></article></section>
  </div>;
}
