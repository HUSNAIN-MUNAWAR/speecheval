export type Run = {
  id: string;
  name: string;
  status: string;
  project_id: string;
  dataset_version_id: string;
  regression_decision: string | null;
  selected_metrics: string[];
  aggregate_metrics: Record<string, unknown>;
  total_items: number;
  processed_items: number;
  execution_profile_id: string;
  manifest_hash: string | null;
  current_stage: string | null;
  created_at: string;
};

export type ComparisonMetric = {
  metric_id: string;
  baseline_value: number | null;
  candidate_value: number | null;
  absolute_delta: number | null;
  relative_delta: number | null;
  confidence_interval: { low?: number; high?: number };
  sample_count: number;
  verdict: string;
};

export type ComparisonResult = {
  id: string;
  integrity_status: string;
  integrity_reasons: string[];
  verdict: string;
  metrics: ComparisonMetric[];
};

const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${base}${path}`, {
    ...init,
    headers: { "content-type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `API error ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const platformApi = {
  runs: () => api<{ items: Run[] }>("/evaluation-runs"),
  run: (id: string) => api<Run>(`/evaluation-runs/${id}`),
  enqueue: (id: string) => api<{ run_id: string; job_id: string }>(`/evaluation-runs/${id}/enqueue`, { method: "POST" }),
  cancel: (id: string) => api<Run>(`/evaluation-runs/${id}/cancel`, { method: "POST" }),
  samples: (id: string) => api<{ items: Array<{ id: string; sample_key: string; language: string; expected_text: string; transcript: string | null; status: string; reviewed: boolean; metrics: Array<{ id: string; value: number | null; unit: string | null; status: string; warnings: string[] }> }> }>(`/evaluation-runs/${id}/samples`),
  events: (id: string) => api<{ items: Array<{ sequence: number; type: string; stage: string | null; message: string; level: string }> }>(`/evaluation-runs/${id}/events/history`),
  compare: (candidate_run_id: string, baseline_run_id: string) =>
    api<{
      id: string;
      integrity_status: string;
      integrity_reasons: string[];
      verdict: string;
      metrics?: ComparisonMetric[];
      metric_results?: ComparisonMetric[];
    }>("/compare", { method: "POST", body: JSON.stringify({ candidate_run_id, baseline_run_id }) }).then((result): ComparisonResult => ({
      id: result.id,
      integrity_status: result.integrity_status,
      integrity_reasons: result.integrity_reasons,
      verdict: result.verdict,
      metrics: result.metrics ?? result.metric_results ?? [],
    })),
  system: () => api<{ api: string; database: string; metric_plugin_count: number; workers: { worker_count: number; queued_jobs: number } }>("/system/health"),
  profiles: () => api<{ profiles: Array<{ id: string; display_name: string; capabilities: string[] }> }>("/system/execution-profiles"),
  cards: () => api<{ items: Array<{ id: string; run_id: string; integrity_status: string; manifest_hash: string | null; created_at: string }> }>("/benchmark-cards"),
  studies: () => api<{ items: Array<{ id: string; title: string; state: string; test_type: string }> }>("/listening-studies"),
};
