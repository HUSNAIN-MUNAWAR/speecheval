from __future__ import annotations

from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import router
from app.core.config import get_settings
from app.db.base import Base
from app.db.seed import seed_demo_data
from app.db.session import SessionLocal, engine
from app.observability.logging import configure_logging

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    settings.artifact_root.mkdir(parents=True, exist_ok=True)
    if settings.is_development:
        Base.metadata.create_all(engine)
        if settings.demo_mode:
            with SessionLocal() as db:
                seed_demo_data(db)
    yield


app = FastAPI(
    title="SpeechEval API",
    version="0.1.0",
    description="CPU-first reproducible TTS evaluation platform API.",
    lifespan=lifespan,
    openapi_url=f"{settings.api_prefix}/openapi.json",
    docs_url="/docs",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = request.headers.get("x-request-id", str(uuid4()))
    response = await call_next(request)
    response.headers["x-request-id"] = request.state.request_id
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "code": "request_validation_error",
            "message": "The request could not be validated.",
            "request_id": getattr(request.state, "request_id", "unknown"),
            "details": {"errors": exc.errors()},
        },
    )


app.include_router(router, prefix=settings.api_prefix)
