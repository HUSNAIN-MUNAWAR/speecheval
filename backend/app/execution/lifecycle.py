from __future__ import annotations

from app.models.entities import RunStatus
from app.services.errors import DomainValidationError

_TRANSITIONS: dict[RunStatus, set[RunStatus]] = {
    RunStatus.DRAFT: {RunStatus.VALIDATING, RunStatus.CANCELLED},
    RunStatus.VALIDATING: {RunStatus.QUEUED, RunStatus.FAILED, RunStatus.CANCELLED},
    RunStatus.QUEUED: {RunStatus.PREPARING, RunStatus.CANCELLED},
    RunStatus.PREPARING: {RunStatus.RUNNING, RunStatus.FAILED, RunStatus.CANCELLED},
    RunStatus.RUNNING: {RunStatus.AGGREGATING, RunStatus.PARTIAL, RunStatus.FAILED, RunStatus.CANCELLED},
    RunStatus.AGGREGATING: {RunStatus.COMPARING, RunStatus.PARTIAL, RunStatus.FAILED},
    RunStatus.COMPARING: {RunStatus.REPORTING, RunStatus.PARTIAL, RunStatus.FAILED},
    RunStatus.REPORTING: {RunStatus.COMPLETED, RunStatus.PARTIAL, RunStatus.FAILED},
    RunStatus.FINALIZING: {RunStatus.COMPLETED, RunStatus.PARTIAL, RunStatus.FAILED},
    RunStatus.COMPLETED: set(),
    RunStatus.PARTIAL: set(),
    RunStatus.FAILED: set(),
    RunStatus.CANCELLED: set(),
}


def transition_run(run, target: RunStatus) -> None:
    if target not in _TRANSITIONS[run.status]:
        raise DomainValidationError(f"Invalid evaluation run transition: {run.status} -> {target}.")
    run.status = target
    run.current_stage = target.value
