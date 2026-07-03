"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Database,
  FlaskConical,
  Gauge,
  GitCompareArrows,
  Code2,
  LayoutDashboard,
  Settings2,
  ShieldCheck,
  Sparkles,
  Waves,
} from "lucide-react";
const links = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/projects", label: "Projects", icon: FlaskConical },
  { href: "/datasets", label: "Datasets", icon: Database },
  { href: "/models", label: "Models", icon: Waves },
  { href: "/runs", label: "Evaluation Runs", icon: Gauge },
  { href: "/compare", label: "Compare", icon: GitCompareArrows },
  { href: "/regression-gates", label: "Regression Gates", icon: ShieldCheck },
  { href: "/benchmarks", label: "Benchmarks", icon: BarChart3 },
  { href: "/listening-lab", label: "Listening Lab", icon: Waves },
  { href: "/system", label: "System Health", icon: Gauge },
];
export function Sidebar({
  compact,
  onCompactChange,
}: {
  compact: boolean;
  onCompactChange: (v: boolean) => void;
}) {
  const path = usePathname();
  return (
    <aside
      className={`sticky top-0 hidden h-screen border-r border-line/80 bg-surface/70 p-3 backdrop-blur lg:flex lg:flex-col ${compact ? "w-[76px]" : "w-[264px]"}`}
    >
      <div className="flex min-h-11 items-center gap-3 px-2">
        <div className="grid h-9 w-9 place-items-center rounded-xl bg-accent text-slate-950 shadow-lg shadow-indigo-500/20">
          <Sparkles size={18} />
        </div>
        {!compact && (
          <div>
            <p className="font-semibold tracking-tight">SpeechEval</p>
            <p className="mono text-[10px] text-muted">
              QUALITY INFRASTRUCTURE
            </p>
          </div>
        )}
      </div>
      {!compact && (
        <button
          type="button"
          className="mt-6 flex items-center justify-between rounded-xl border border-line bg-panel px-3 py-2.5 text-left"
        >
          <span>
            <span className="block text-xs text-muted">Workspace</span>
            <span className="block text-sm font-medium">Demo Speech Lab</span>
          </span>
          <ChevronRight size={16} className="text-muted" />
        </button>
      )}
      <nav className="mt-6 space-y-1" aria-label="Main navigation">
        {links.map(({ href, label, icon: Icon }) => {
          const active =
            (href === "/" && label === "Overview" && path === "/") ||
            (href !== "/" && path.startsWith(href));
          return (
            <Link
              key={label}
              href={href}
              title={compact ? label : undefined}
              className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${active ? "bg-accent/15 text-indigo-200" : "text-muted hover:bg-white/[.04] hover:text-ink"}`}
            >
              <Icon size={17} />
              <span className={compact ? "sr-only" : ""}>{label}</span>
              {label === "Evaluation Runs" && !compact && (
                <span className="ml-auto rounded-full bg-warning/15 px-2 py-0.5 text-[10px] font-semibold text-warning">
                  3
                </span>
              )}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto space-y-1 border-t border-line pt-3">
        {[
          { label: "Settings", icon: Settings2 },
          { label: "Documentation", icon: BookOpen },
          { label: "GitHub", icon: Code2 },
        ].map(({ label, icon: Icon }) => (
          <button
            key={label}
            type="button"
            title={compact ? label : undefined}
            disabled
            className="flex w-full cursor-not-allowed items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-muted opacity-75"
          >
            <Icon size={17} />
            <span className={compact ? "sr-only" : ""}>{label}</span>
          </button>
        ))}
        <button
          type="button"
          onClick={() => onCompactChange(!compact)}
          className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-muted transition hover:bg-white/[.04] hover:text-ink"
        >
          {compact ? <ChevronRight size={17} /> : <ChevronLeft size={17} />}
          <span className={compact ? "sr-only" : ""}>Collapse sidebar</span>
        </button>
      </div>
    </aside>
  );
}
