"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import snapshot
from .config import settings
from .routers import diff, instances, providers, recommend


TAGS_METADATA = [
    {"name": "recommend", "description": "Rank machine types for a workload profile."},
    {"name": "instances", "description": "Browse and filter the bundled machine-type snapshot."},
    {"name": "providers", "description": "Summaries of the providers present in the snapshot."},
    {"name": "diff", "description": "Compare recommendations for two workloads — useful for migration planning."},
    {"name": "meta", "description": "Service metadata and health checks."},
]

DESCRIPTION = """
Stateless HTTP API over [cloudfit-core](https://github.com/cloudfit-io/cloudfit-core).
Scores cloud machine types against a workload profile using a **bundled provider
snapshot** — no database, no cloud credentials.

**Try it:** expand `POST /recommend` below, click *Try it out* (a runnable example
is pre-filled), and *Execute*. Hard floors (RAM / vCPU / GPU) are applied before
scoring; `optimize_for` is one of `cost`, `balanced`, `performance`, `availability`.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm the snapshot cache once at startup so the first request is fast.
    snapshot.load_snapshot()
    yield


app = FastAPI(
    title=settings.title,
    version=settings.version,
    summary=settings.description,
    description=DESCRIPTION,
    lifespan=lifespan,
    openapi_tags=TAGS_METADATA,
    contact={"name": "Chaitanya Krishna Kasaraneni", "url": "https://ckasaraneni.com"},
    license_info={"name": "Apache-2.0", "url": "https://www.apache.org/licenses/LICENSE-2.0"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommend.router)
app.include_router(instances.router)
app.include_router(providers.router)
app.include_router(diff.router)


@app.get("/", tags=["meta"], summary="Service metadata")
def root() -> dict:
    return {
        "name": settings.title,
        "version": settings.version,
        "instances": len(snapshot.all_instances()),
        "docs": "/docs",
    }


@app.get("/health", tags=["meta"], summary="Health check")
def health() -> dict:
    return {"status": "ok"}
