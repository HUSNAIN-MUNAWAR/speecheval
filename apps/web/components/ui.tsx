import { ArrowDownRight, ArrowUpRight } from "lucide-react";
export function StatusBadge({
  status,
}: {
  status: "pass" | "warning" | "fail" | "draft";
}) {
  const style = {
    pass: "border-success/25 bg-success/10 text-emerald-200",
    warning: "border-warning/25 bg-warning/10 text-amber-200",
    fail: "border-danger/25 bg-danger/10 text-rose-200",
    draft: "border-line bg-white/[.03] text-muted",
  }[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-1 text-[10px] font-bold uppercase tracking-[.12em] ${style}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {status}
    </span>
  );
}
export function MetricCard({
  label,
  value,
  delta,
  tone = "neutral",
  footnote,
}: {
  label: string;
  value: string;
  delta?: string;
  tone?: "good" | "bad" | "neutral";
  footnote: string;
}) {
  const cls =
    tone === "good"
      ? "text-emerald-300"
      : tone === "bad"
        ? "text-rose-300"
        : "text-muted";
  return (
    <article className="panel p-4">
      <p className="eyebrow">{label}</p>
      <div className="mt-3 flex items-end justify-between gap-2">
        <p className="mono text-2xl font-semibold tracking-[-.05em]">{value}</p>
        {delta && (
          <span
            className={`flex items-center gap-0.5 text-xs font-semibold ${cls}`}
          >
            {tone === "bad" ? (
              <ArrowUpRight size={13} />
            ) : (
              <ArrowDownRight size={13} />
            )}{" "}
            {delta}
          </span>
        )}
      </div>
      <p className="mt-3 text-xs text-muted">{footnote}</p>
    </article>
  );
}
export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action: string;
}) {
  return (
    <div className="mb-7 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-[-.035em]">
          {title}
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
          {description}
        </p>
      </div>
      <span className="inline-flex w-fit rounded-xl border border-line bg-surface px-3.5 py-2.5 text-sm font-semibold text-muted">
        {action}
      </span>
    </div>
  );
}
