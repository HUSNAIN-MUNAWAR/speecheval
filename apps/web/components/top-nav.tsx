import { Plus, Search, Wifi } from "lucide-react";
export function TopNav() {
  return (
    <header className="sticky top-0 z-20 flex h-[66px] items-center justify-between border-b border-line/80 bg-canvas/80 px-4 backdrop-blur-xl sm:px-6 lg:px-8">
      <button
        type="button"
        disabled
        className="hidden cursor-not-allowed items-center gap-3 rounded-xl border border-line bg-panel px-3 py-2 text-sm text-muted md:flex"
      >
        <Search size={16} />
        <span>Command palette · Phase 1</span>
        <kbd className="mono rounded border border-line px-1.5 py-.5 text-[10px]">
          ⌘ K
        </kbd>
      </button>
      <span className="font-semibold md:hidden">SpeechEval</span>
      <div className="ml-auto flex items-center gap-2">
        <span className="hidden items-center gap-2 rounded-full border border-success/25 bg-success/10 px-3 py-1.5 text-xs font-medium text-emerald-200 sm:flex">
          <Wifi size={13} />
          API contract ready
        </span>
        <button
          type="button"
          disabled
          className="inline-flex cursor-not-allowed items-center gap-2 rounded-xl bg-accent/80 px-3.5 py-2 text-sm font-semibold text-slate-950"
        >
          <Plus size={16} />
          <span className="hidden sm:inline">Create · Phase 1</span>
        </button>
        <div
          aria-label="User Husnain Munawar"
          className="grid h-9 w-9 place-items-center rounded-full border border-line bg-panel text-xs font-semibold"
        >
          HM
        </div>
      </div>
    </header>
  );
}
