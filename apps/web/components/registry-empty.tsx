import { Database, RadioTower } from "lucide-react";
export function RegistryEmpty({ kind }: { kind: "dataset" | "model" }) {
  const data = kind === "dataset";
  return (
    <section className="panel grid-lines grid min-h-[340px] place-items-center p-6 text-center">
      <div className="max-w-md">
        <div className="mx-auto grid h-12 w-12 place-items-center rounded-2xl border border-line bg-surface text-accent">
          {data ? <Database size={22} /> : <RadioTower size={22} />}
        </div>
        <h2 className="mt-5 text-lg font-semibold">
          {data
            ? "Dataset registry is API-ready"
            : "Model registry is API-ready"}
        </h2>
        <p className="mt-2 text-sm leading-6 text-muted">
          {data
            ? "Versioned manifests, structural validation, hashes, and language coverage are implemented. File upload and audio validation enter Phase 2."
            : "Model metadata and immutable version provenance are implemented. Benchmark history is populated once the evaluation worker arrives."}
        </p>
        <p className="mt-5 inline-flex rounded-lg border border-line bg-surface px-3 py-2 mono text-xs text-muted">
          Demo Data is seeded in local development.
        </p>
      </div>
    </section>
  );
}
