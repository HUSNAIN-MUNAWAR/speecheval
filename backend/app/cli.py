from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

import typer
from sqlalchemy import select

from app.comparison.service import create_comparison
from app.db.seed import main as seed_main
from app.db.session import SessionLocal
from app.execution.runtime import create_evaluation_job, request_cancel
from app.metrics import registry
from app.models.entities import Baseline, EvaluationEvent, EvaluationRun, RegressionPolicy
from app.reporting.cards import create_benchmark_card
from app.services.domain import stable_hash, validate_manifest_items
from app.services.evidence import create_baseline, evaluate_policy, freeze_baseline
from app.workers.queue import dispatch_evaluation_job
from app.workers.worker import run_worker_forever

app=typer.Typer(help="SpeechEval reproducible speech reliability CLI.",no_args_is_help=True)
demo_app=typer.Typer();dataset_app=typer.Typer();run_app=typer.Typer();worker_app=typer.Typer();baseline_app=typer.Typer();policy_app=typer.Typer();plugin_app=typer.Typer();ci_app=typer.Typer()
app.add_typer(demo_app,name="demo");app.add_typer(dataset_app,name="dataset");app.add_typer(run_app,name="run");app.add_typer(worker_app,name="worker");app.add_typer(baseline_app,name="baseline");app.add_typer(policy_app,name="policy");app.add_typer(plugin_app,name="plugin");app.add_typer(ci_app,name="ci")


def out(payload:object,as_json:bool=True)->None:
    typer.echo(json.dumps(payload,ensure_ascii=False,indent=2,default=str) if as_json else str(payload))


@app.command("init")
def init()->None:typer.echo("SpeechEval initialized. Copy .env.example to .env, run migrations, then seed demo data.")


@demo_app.command("seed")
def demo_seed()->None:seed_main()


@dataset_app.command("validate")
def dataset_validate(path:Path)->None:
    import yaml
    payload=yaml.safe_load(path.read_text()) if path.suffix.lower() in {".yaml",".yml"} else json.loads(path.read_text())
    errors=validate_manifest_items(payload.get("items",[]));out({"valid":not errors,"errors":errors,"item_count":len(payload.get("items",[]))})
    raise typer.Exit(0 if not errors else 2)


@dataset_app.command("fingerprint")
def dataset_fingerprint(path:Path)->None:
    import yaml
    payload=yaml.safe_load(path.read_text()) if path.suffix.lower() in {".yaml",".yml"} else json.loads(path.read_text())
    out({"path":str(path),"content_hash":stable_hash(payload)})


@worker_app.command("start")
def worker_start()->None:run_worker_forever()


@worker_app.command("status")
def worker_status()->None:
    from app.models.entities import Worker
    with SessionLocal() as db:out({"workers":[{"id":str(w.id),"key":w.worker_key,"profile":w.profile_id,"status":w.status.value,"last_heartbeat_at":w.last_heartbeat_at} for w in db.scalars(select(Worker))]})


@run_app.command("enqueue")
def run_enqueue(run_id:str,wait:bool=True)->None:
    with SessionLocal() as db:
        run=db.get(EvaluationRun,UUID(run_id))
        if not run:raise typer.BadParameter("Run not found.")
        job=create_evaluation_job(db,run);payload={"run_id":str(run.id),"job_id":str(job.id),"status":run.status.value}
    dispatch_evaluation_job(job.id,wait_for_inline=wait);out(payload)


@run_app.command("cancel")
def run_cancel(run_id:str)->None:
    with SessionLocal() as db:
        run=db.get(EvaluationRun,UUID(run_id))
        if not run:raise typer.BadParameter("Run not found.")
        request_cancel(db,run);out({"run_id":run_id,"cancellation_requested":True})


@run_app.command("status")
def run_status(run_id:str)->None:
    with SessionLocal() as db:
        run=db.get(EvaluationRun,UUID(run_id))
        if not run:raise typer.BadParameter("Run not found.")
        out({"run_id":str(run.id),"status":run.status.value,"processed_items":run.processed_items,"total_items":run.total_items,"decision":run.regression_decision,"manifest_hash":run.manifest_hash})


@run_app.command("watch")
def run_watch(run_id:str)->None:
    with SessionLocal() as db:
        events=list(db.scalars(select(EvaluationEvent).where(EvaluationEvent.run_id==UUID(run_id)).order_by(EvaluationEvent.sequence)))
        for event in events:typer.echo(f"{event.sequence:03d} {event.level:<5} {event.stage or '-':<12} {event.message}")


@run_app.command("inspect")
def run_inspect(run_id:str)->None:
    with SessionLocal() as db:
        run=db.get(EvaluationRun,UUID(run_id))
        if not run:raise typer.BadParameter("Run not found.")
        out({"run_id":str(run.id),"manifest":run.immutable_manifest,"aggregates":run.aggregate_metrics,"failure_reason":run.failure_reason})


@run_app.command("benchmark-card")
def run_benchmark_card(run_id:str)->None:
    with SessionLocal() as db:
        run=db.get(EvaluationRun,UUID(run_id))
        if not run:raise typer.BadParameter("Run not found.")
        card=create_benchmark_card(db,run);typer.echo(card.markdown)


@run_app.command("export")
def run_export(run_id:str,format:str="markdown")->None:
    with SessionLocal() as db:
        run=db.get(EvaluationRun,UUID(run_id))
        if not run:raise typer.BadParameter("Run not found.")
        if format=="json":out({"run_id":str(run.id),"manifest":run.immutable_manifest,"aggregates":run.aggregate_metrics})
        elif format=="markdown":typer.echo(create_benchmark_card(db,run).markdown)
        else:raise typer.BadParameter("Only markdown and json exports are implemented.")


@app.command("compare")
def compare(run_a:str,run_b:str,strict:bool=False)->None:
    with SessionLocal() as db:
        candidate=db.get(EvaluationRun,UUID(run_a));baseline=db.get(EvaluationRun,UUID(run_b))
        if not candidate or not baseline:raise typer.BadParameter("Both runs must exist.")
        comparison=create_comparison(db,candidate,baseline)
        out({"id":str(comparison.id),"integrity":comparison.integrity_status,"verdict":comparison.verdict,"reasons":comparison.integrity_reasons})
        if strict and comparison.integrity_status!="STRICTLY_COMPARABLE":raise typer.Exit(2)


@baseline_app.command("create")
def baseline_create(run:str,name:str="CLI baseline")->None:
    with SessionLocal() as db:
        evaluation=db.get(EvaluationRun,UUID(run))
        if not evaluation:raise typer.BadParameter("Run not found.")
        baseline=create_baseline(db,evaluation.project_id,evaluation,name);out({"id":str(baseline.id),"run_id":str(baseline.run_id)})


@baseline_app.command("freeze")
def baseline_freeze(baseline_id:str)->None:
    with SessionLocal() as db:
        baseline=db.get(Baseline,UUID(baseline_id))
        if not baseline:raise typer.BadParameter("Baseline not found.")
        freeze_baseline(db,baseline);out({"id":str(baseline.id),"is_frozen":baseline.is_frozen})


@policy_app.command("create")
def policy_create(file:Path)->None:
    import yaml
    payload=yaml.safe_load(file.read_text())
    with SessionLocal() as db:
        policy=RegressionPolicy(**payload);db.add(policy);db.commit();db.refresh(policy);out({"id":str(policy.id),"name":policy.name})


@policy_app.command("test")
def policy_test(policy_id:str,run_id:str)->None:
    with SessionLocal() as db:
        policy=db.get(RegressionPolicy,UUID(policy_id));run=db.get(EvaluationRun,UUID(run_id))
        if not policy or not run:raise typer.BadParameter("Policy or run not found.")
        result=evaluate_policy(db,policy,run);db.add(result);db.commit();out({"decision":result.decision,"explanation":result.explanation,"integrity":result.integrity_status})


@plugin_app.command("list")
def plugin_list()->None:out(registry.describe_all())


@plugin_app.command("inspect")
def plugin_inspect(plugin_id:str)->None:
    plugin=registry.get(plugin_id)
    if not plugin:raise typer.BadParameter("Plugin not found.")
    out(next(item for item in registry.describe_all() if item["id"]==plugin_id))


@plugin_app.command("validate")
def plugin_validate()->None:
    unavailable=[]
    from app.metrics.base import EvaluationContext
    for plugin in registry.plugins.values():
        available,reason=plugin.is_available(EvaluationContext("local-cpu-lightweight","."))
        if not available:unavailable.append({"id":plugin.id,"reason":reason})
    out({"valid":not unavailable,"unavailable":unavailable,"plugin_count":len(registry.plugins)})


@ci_app.command("evaluate")
def ci_evaluate(candidate_run:str,baseline_run:str)->None:
    with SessionLocal() as db:
        candidate=db.get(EvaluationRun,UUID(candidate_run));baseline=db.get(EvaluationRun,UUID(baseline_run))
        if not candidate or not baseline:raise typer.BadParameter("Candidate and baseline runs must exist.")
        comparison=create_comparison(db,candidate,baseline)
        typer.echo("## SpeechEval Regression Report\n\n"+f"Status: **{comparison.verdict}**\n\nIntegrity: **{comparison.integrity_status}**\n")
        if comparison.verdict=="LIKELY_REGRESSION" or comparison.integrity_status=="NOT_COMPARABLE":raise typer.Exit(2)


if __name__ == "__main__":
    app()
