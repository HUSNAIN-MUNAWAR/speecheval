from __future__ import annotations

import random
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import (
    EvaluationCase,
    EvaluationRun,
    ListeningResponse,
    ListeningStudy,
    ListeningTask,
)
from app.services.errors import DomainValidationError


def create_study(db:Session, *, project_id:UUID, title:str, description:str|None, test_type:str, linked_run_ids:list[UUID], selected_sample_keys:list[str], rating_scale:dict, rater_instructions:str|None, consent_notice:str|None, randomization_seed:int, anonymity_enabled:bool, response_limit:int|None)->ListeningStudy:
    runs=[db.get(EvaluationRun,run_id) for run_id in linked_run_ids]
    if any(run is None or run.project_id!=project_id for run in runs):raise DomainValidationError("Every linked run must exist and belong to the study project.")
    if test_type in {"AB_PREFERENCE","ABX"} and len(runs)!=2:raise DomainValidationError("A/B and ABX studies require exactly two runs.")
    study=ListeningStudy(project_id=project_id,title=title,description=description,test_type=test_type,linked_run_ids=[str(value) for value in linked_run_ids],selected_sample_keys=selected_sample_keys,rating_scale=rating_scale,rater_instructions=rater_instructions,consent_notice=consent_notice,randomization_seed=randomization_seed,anonymity_enabled=anonymity_enabled,response_limit=response_limit)
    db.add(study);db.commit();db.refresh(study);return study


def activate_study(db:Session,study:ListeningStudy)->ListeningStudy:
    if study.state not in {"DRAFT","PAUSED"}:raise DomainValidationError("Only draft or paused studies can be activated.")
    if db.scalar(select(func.count()).select_from(ListeningTask).where(ListeningTask.study_id==study.id))==0:
        run_ids=[UUID(value) for value in study.linked_run_ids];cases_by_run=[]
        for run_id in run_ids:
            cases_by_run.append({case.sample_key:case for case in db.scalars(select(EvaluationCase).where(EvaluationCase.run_id==run_id))})
        keys=study.selected_sample_keys or sorted(set.intersection(*(set(mapping) for mapping in cases_by_run)))
        rng=random.Random(study.randomization_seed)
        for order,key in enumerate(keys,1):
            first=cases_by_run[0].get(key); second=cases_by_run[1].get(key) if len(cases_by_run)>1 else None
            if first is None:continue
            a={"case_id":str(first.id),"audio_ref":first.metric_summary_json.get("audio_ref"),"run_id":str(first.run_id)}
            b={"case_id":str(second.id),"audio_ref":second.metric_summary_json.get("audio_ref"),"run_id":str(second.run_id)} if second else {}
            if second and rng.choice([True,False]):a,b=b,a
            db.add(ListeningTask(study_id=study.id,task_order=order,sample_key=key,expected_text=first.expected_text,option_a_json=a,option_b_json=b,option_x_json={},randomization_token=f"{study.randomization_seed}-{order}-{key}"))
    study.state="ACTIVE";db.commit();db.refresh(study);return study


def public_tasks(db:Session,study:ListeningStudy)->list[dict]:
    tasks=list(db.scalars(select(ListeningTask).where(ListeningTask.study_id==study.id).order_by(ListeningTask.task_order)))
    return [{"id":str(task.id),"order":task.task_order,"sample_key":task.sample_key,"expected_text":task.expected_text,"option_a":{"label":"A"},"option_b":{"label":"B"} if task.option_b_json else None} for task in tasks]


def submit_response(db:Session,study:ListeningStudy,*,task_id:UUID,rater_key:str,preference:str|None,rating:float|None,confidence:int|None,note:str|None,duration_ms:int|None)->ListeningResponse:
    if study.state!="ACTIVE":raise DomainValidationError("Listening study is not active.")
    task=db.get(ListeningTask,task_id)
    if task is None or task.study_id!=study.id:raise DomainValidationError("Task does not belong to this study.")
    if study.response_limit is not None:
        count=db.scalar(select(func.count()).select_from(ListeningResponse).where(ListeningResponse.study_id==study.id,ListeningResponse.rater_key==rater_key)) or 0
        if count>=study.response_limit:raise DomainValidationError("The study response limit has been reached for this rater.")
    duplicate=db.scalar(select(ListeningResponse).where(ListeningResponse.study_id==study.id,ListeningResponse.task_id==task.id,ListeningResponse.rater_key==rater_key))
    if duplicate:raise DomainValidationError("This rater already answered this task.")
    response=ListeningResponse(study_id=study.id,task_id=task.id,rater_key=rater_key,preference=preference,rating=rating,confidence=confidence,note=note,duration_ms=duration_ms)
    db.add(response);db.commit();db.refresh(response);return response


def results(db:Session,study:ListeningStudy)->dict:
    rows=list(db.scalars(select(ListeningResponse).where(ListeningResponse.study_id==study.id)))
    counts={"A":0,"B":0,"X":0,"NO_PREFERENCE":0}
    for row in rows:
        if row.preference in counts:counts[row.preference]+=1
    ratings=[row.rating for row in rows if row.rating is not None]
    return {"study_id":str(study.id),"state":study.state,"response_count":len(rows),"preferences":counts,"mean_rating":sum(ratings)/len(ratings) if ratings else None,"limitations":["Exploratory internal feedback. Results are not a generalized scientific study without a defined recruitment and calibration protocol.","Agreement estimates are unavailable unless sufficient independent raters complete overlapping tasks."]}
