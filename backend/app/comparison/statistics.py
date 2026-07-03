from __future__ import annotations

import random
import statistics
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BootstrapEstimate:
    baseline_mean: float
    candidate_mean: float
    absolute_delta: float
    relative_delta: float | None
    ci_low: float
    ci_high: float
    sample_count: int


def paired_bootstrap(baseline: list[float], candidate: list[float], *, iterations: int = 1000, seed: int = 42) -> BootstrapEstimate:
    if len(baseline) != len(candidate) or not baseline:
        raise ValueError("Paired bootstrap requires non-empty matched samples.")
    deltas=[c-b for b,c in zip(baseline,candidate, strict=True)]
    rng=random.Random(seed); estimates=[]
    for _ in range(iterations):
        sample=[deltas[rng.randrange(len(deltas))] for _ in deltas]
        estimates.append(statistics.fmean(sample))
    estimates.sort(); lower=estimates[int(.025*(len(estimates)-1))]; upper=estimates[int(.975*(len(estimates)-1))]
    bmean=statistics.fmean(baseline); cmean=statistics.fmean(candidate); delta=cmean-bmean
    return BootstrapEstimate(bmean,cmean,delta,delta/bmean if bmean else None,lower,upper,len(deltas))
