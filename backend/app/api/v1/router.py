from fastapi import APIRouter

from app.api.v1 import (
    baselines,
    benchmark_cards,
    comparisons,
    datasets,
    health,
    listening_studies,
    models,
    policies,
    projects,
    runs,
    system,
)

router = APIRouter()
router.include_router(health.router, tags=["Health"])
router.include_router(projects.router, prefix="/projects", tags=["Projects"])
router.include_router(datasets.router, prefix="/datasets", tags=["Datasets"])
router.include_router(models.router, prefix="/models", tags=["Models"])
router.include_router(runs.router, prefix="/evaluation-runs", tags=["Evaluation Runs"])
router.include_router(comparisons.router, prefix="/compare", tags=["Compare Lab"])
router.include_router(baselines.router, prefix="/baselines", tags=["Baselines"])
router.include_router(policies.router, prefix="/regression-policies", tags=["Regression Gates"])
router.include_router(listening_studies.router, prefix="/listening-studies", tags=["Listening Lab"])
router.include_router(benchmark_cards.router, prefix="/benchmark-cards", tags=["Benchmark Cards"])
router.include_router(system.router, prefix="/system", tags=["System"])
