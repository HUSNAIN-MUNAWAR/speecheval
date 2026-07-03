import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  CheckCircle2,
  Clock3,
  Files,
  Gauge,
  TrendingDown,
} from "lucide-react";
import { MetricCard, StatusBadge } from "@/components/ui";
const trend = [38, 44, 40, 57, 51, 68, 64, 72, 77, 71, 82, 88];
const activity = [
  {
    title: "Candidate fixture failure completed",
    meta: "FixtureVoice 1.0.0 · 5 samples · Mock Metric",
    status: "fail" as const,
    time: "12m ago",
  },
  {
    title: "Narration Fixture Set v1.0 imported",
    meta: "5 languages · SHA256 pinned · Synthetic Fixture",
    status: "pass" as const,
    time: "48m ago",
  },
  {
    title: "Regression policy preview",
    meta: "Phase 4 implementation boundary",
    status: "warning" as const,
    time: "2h ago",
  },
];
export function OverviewDashboard() {
  return (
    <div className="space-y-5">
      <section className="relative overflow-hidden rounded-2xl border border-line bg-panel p-5 sm:p-7">
        <div className="absolute inset-0 grid-lines opacity-50" />
        <div className="relative flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
          <div>
            <p className="eyebrow">Demo Speech Lab · Demo Data</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-[-.04em] sm:text-4xl">
              Quality signals, not guesswork.
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">
              A reproducibility-first workspace for TTS quality, latency, and
              regression evidence. The fixture values below are explicitly
              mocked, never presented as model results.
            </p>
          </div>
          <div className="flex items-center gap-3 rounded-xl border border-accent/20 bg-accent/10 px-4 py-3">
            <Activity className="text-indigo-200" size={20} />
            <div>
              <p className="text-xs text-indigo-100/70">
                Latest fixture checkpoint
              </p>
              <p className="mono text-sm font-semibold text-indigo-100">
                PASS · baseline
              </p>
            </div>
          </div>
        </div>
      </section>
      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Regression pass rate"
          value="92.4%"
          delta="2.1%"
          tone="good"
          footnote="Last 30 synthetic runs"
        />
        <MetricCard
          label="Median mock WER"
          value="4.2%"
          delta="0.6%"
          tone="good"
          footnote="Lower is better · Demo Data"
        />
        <MetricCard
          label="Median latency"
          value="284ms"
          delta="11ms"
          tone="bad"
          footnote="Fixture workload p50"
        />
        <MetricCard
          label="Language coverage"
          value="5 / 5"
          footnote="Synthetic multilingual fixture"
        />
      </section>
      <section className="grid gap-5 xl:grid-cols-[1.55fr_1fr]">
        <article className="panel p-5">
          <p className="eyebrow">Benchmark trend · Mock Metric</p>
          <h2 className="mt-1 text-lg font-semibold">
            Quality score across fixture runs
          </h2>
          <div
            className="mt-7 flex h-48 items-end gap-2"
            aria-label="Synthetic benchmark trend"
          >
            {trend.map((value, index) => (
              <div
                key={`${value}-${index}`}
                className="group relative flex-1 rounded-t-md bg-gradient-to-t from-accent/35 to-accent/80 transition hover:from-accent/60 hover:to-accent"
                style={{ height: `${value}%` }}
              >
                <span className="absolute -top-6 left-1/2 hidden -translate-x-1/2 rounded bg-surface px-1.5 py-.5 mono text-[10px] text-muted group-hover:block">
                  {value}
                </span>
              </div>
            ))}
          </div>
          <div className="mt-4 flex items-center justify-between border-t border-line pt-4 text-xs text-muted">
            <span>May 12</span>
            <span className="inline-flex items-center gap-1.5 text-emerald-300">
              <TrendingDown size={13} />
              Lower WER is better
            </span>
            <span>Jun 29</span>
          </div>
        </article>
        <article className="panel p-5">
          <p className="eyebrow">Worker health</p>
          <h2 className="mt-1 text-lg font-semibold">Local topology</h2>
          <div className="mt-5 space-y-3">
            <Health
              icon={<CheckCircle2 size={16} />}
              label="API contract"
              detail="reachable"
              tone="success"
            />
            <Health
              icon={<Files size={16} />}
              label="Artifact root"
              detail="local filesystem boundary"
              tone="success"
            />
            <Health
              icon={<Clock3 size={16} />}
              label="Evaluation worker"
              detail="queue execution · Phase 2"
              tone="warning"
            />
          </div>
          <p className="mt-5 rounded-xl border border-line bg-surface p-3 mono text-[11px] text-muted">
            CPU-first · SQLite fallback · no GPU required
          </p>
        </article>
      </section>
      <section className="grid gap-5 xl:grid-cols-[1.35fr_1fr]">
        <article className="panel overflow-hidden">
          <div className="flex items-center justify-between p-5">
            <div>
              <p className="eyebrow">Recent activity</p>
              <h2 className="mt-1 text-lg font-semibold">
                Run and registry events
              </h2>
            </div>
            <span className="text-sm font-medium text-indigo-200">
              API-seeded <ArrowUpRight className="inline" size={14} />
            </span>
          </div>
          <div className="divide-y divide-line">
            {activity.map((item) => (
              <div
                key={item.title}
                className="flex items-center gap-3 px-5 py-4"
              >
                <StatusBadge status={item.status} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{item.title}</p>
                  <p className="mt-1 truncate text-xs text-muted">
                    {item.meta}
                  </p>
                </div>
                <time className="mono text-[11px] text-muted">{item.time}</time>
              </div>
            ))}
          </div>
        </article>
        <article className="panel p-5">
          <p className="eyebrow">Attention required</p>
          <h2 className="mt-1 text-lg font-semibold">Fixture gate preview</h2>
          <div className="mt-5 space-y-3">
            <Alert
              title="Mock WER delta"
              detail="+8.4% vs baseline · threshold +3.0%"
            />
            <Alert
              title="Latency ceiling"
              detail="516ms p50 · threshold 420ms"
            />
          </div>
          <button
            disabled
            className="mt-5 cursor-not-allowed rounded-xl border border-line px-3 py-2 text-sm text-muted"
          >
            <Gauge className="mr-2 inline" size={15} />
            Regression engine · Phase 4
          </button>
        </article>
      </section>
    </div>
  );
}
function Health({
  icon,
  label,
  detail,
  tone,
}: {
  icon: React.ReactNode;
  label: string;
  detail: string;
  tone: "success" | "warning";
}) {
  return (
    <div className="flex items-center gap-3">
      <span
        className={tone === "success" ? "text-emerald-300" : "text-amber-300"}
      >
        {icon}
      </span>
      <div className="flex-1">
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-muted">{detail}</p>
      </div>
      <span
        className={`h-2 w-2 rounded-full ${tone === "success" ? "bg-success" : "bg-warning"}`}
      />
    </div>
  );
}
function Alert({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="rounded-xl border border-danger/20 bg-danger/[.07] p-3">
      <div className="flex gap-2">
        <AlertTriangle size={16} className="mt-.5 shrink-0 text-rose-300" />
        <div>
          <p className="text-sm font-medium text-rose-100">{title}</p>
          <p className="mt-1 text-xs leading-5 text-rose-200/65">{detail}</p>
        </div>
      </div>
    </div>
  );
}
