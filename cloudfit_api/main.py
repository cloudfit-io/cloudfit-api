"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import snapshot
from .config import settings
from .routers import diff, instances, providers, recommend


TAGS_METADATA = [
    {"name": "recommend", "description": "Score a workload against the catalog and get ranked machine-type picks."},
    {"name": "diff", "description": "Compare two workloads. The delta surfaces what changes in cost, vCPU, and RAM if you move between them."},
    {"name": "instances", "description": "Direct catalog access. Browse the bundled snapshot with filters."},
    {"name": "providers", "description": "Stats about what is in the snapshot. Useful as a sanity check before calling /recommend."},
    {"name": "meta", "description": "Service metadata and liveness probe."},
]

DESCRIPTION = """
**Try it now.** Expand `POST /recommend` below, click *Try it out* (a runnable example
is pre-filled), then *Execute*.

**Prefer a UI?** [chaitanyakasaraneni-cloudfit-ui.hf.space](https://chaitanyakasaraneni-cloudfit-ui.hf.space): same scoring engine, form-based input.

**Notes for callers**
- Hard floors (region, RAM, vCPU, GPU) run before scoring. Under-spec candidates
  appear in the response as `disqualified` with a reason, not silently dropped.
- `optimize_for` accepts `cost`, `balanced`, `performance`, or `availability`.
  As of cloudfit-core 0.3, the performance scorer is fit-based: exact match
  through 1.5x of requested resources scores highest, then decays.
- Cost is normalized across the qualifying candidates: the cheapest scores 1.0
  and the most expensive 0.0, so a real price gap moves the score. A candidate
  with no price (`price_hr` <= 0) scores 0.0 on cost and is never treated as free.
- `archetype` is a classification and disk-sizing label only; it does not change
  ranking in this release (scoring is driven by `optimize_for`).
- `workload.headroom` (default 0) asks for spare capacity above the declared
  vcpu/ram_gb, as a fraction (0.25 = 25% more, i.e. 1.25x). `workload.headroom_mode`
  is `hard` (raise the floor, so instances without the buffer are disqualified) or
  `soft` (prefer the buffer in scoring without disqualifying).
- Pass `candidates` in the request body to score your own catalog instead of
  the bundled snapshot.
- Scoring math: [cloudfit-core](https://github.com/cloudfit-io/cloudfit-core).
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
    """Name, running version, snapshot size, and a pointer to these docs."""
    return {
        "name": settings.title,
        "version": settings.version,
        "instances": len(snapshot.all_instances()),
        "docs": "/docs",
    }


@app.get("/health", tags=["meta"], summary="Liveness probe")
def health() -> dict:
    """Returns `{\"status\": \"ok\"}`. Use for container health checks."""
    return {"status": "ok"}
