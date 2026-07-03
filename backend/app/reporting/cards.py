from __future__ import annotations

import html

from sqlalchemy.orm import Session

from app.comparison.integrity import assess_integrity
from app.models.entities import BenchmarkCard, EvaluationRun


def create_benchmark_card(db:Session,run:EvaluationRun,baseline:EvaluationRun|None=None)->BenchmarkCard:
    integrity=assess_integrity(run,baseline).status.value if baseline else "SELF_DESCRIBED"
    model=run.model_version.model;dataset=run.dataset_version.dataset
    content={"model":{"name":model.name,"version":run.model_version.version,"license":model.license},"dataset":{"name":dataset.name,"version":run.dataset_version.version,"hash":run.dataset_version.manifest_hash,"languages":dataset.language_coverage},"metrics":run.aggregate_metrics,"execution":run.execution_environment,"profile":run.execution_profile_id,"manifest_hash":run.manifest_hash,"integrity":integrity,"limitations":["Results are traceable to the stored manifest and local artifact references.","Mock/manual transcript metrics are labeled and are not ASR evidence."]}
    markdown=f"# SpeechEval Benchmark Card\n\n**Model:** {model.name}@{run.model_version.version}\n\n**Dataset:** {dataset.name} {run.dataset_version.version}\n\n**Integrity:** {integrity}\n\n**Manifest hash:** `{run.manifest_hash}`\n\n## Metrics\n\n```json\n{run.aggregate_metrics}\n```\n\n## Limitations\n\n- Metrics and execution metadata are stored in the immutable manifest.\n- Speaker similarity and live ASR are not inferred when unavailable.\n"
    card=BenchmarkCard(run_id=run.id,integrity_status=integrity,manifest_hash=run.manifest_hash,content_json=content,markdown=markdown,html=f"<article><h1>SpeechEval Benchmark Card</h1><pre>{html.escape(markdown)}</pre></article>")
    db.add(card);db.commit();db.refresh(card);return card
