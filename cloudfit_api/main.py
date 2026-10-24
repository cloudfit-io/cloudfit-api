"""FastAPI application entry point."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import snapshot
from .config import settings
from .limits import BodySizeLimitMiddleware
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
  The performance scorer is fit-based: an exact fit to the requested
  resources scores highest, and oversize decays.
- Cost is scored relative to the cheapest qualifying candidate, which scores 1.0;
  one costing twice as much per unit of work scores 0.5. A candidate with no
  price (`price_hr` <= 0) scores 0.0 on cost and is never treated as free.
- The bundled snapshots cover GCP and AWS. Both are scored by default; set
  `workload.providers` (e.g. `["aws"]`) to limit the clouds, or `region` to one
  region.
- `archetype` sets the per-component perf weighting (e.g. `mem` weights RAM,
  `io` weights local SSD vs `scratch_tb`), so it does influence ranking on top
  of `optimize_for` and the hard floors. For the `gpu` archetype, GPU throughput
  (`gpu_type` via the core `GPU_CLASS` table) is scored, so an A100 outranks a T4
  at equal VRAM.
- `perf_factor` on a candidate scores effective per-vCPU capacity (a faster family
  is not equated with a slower one at the same core count) and makes cost reflect
  cost per unit of work. The bundled snapshot is pre-populated with `perf_factor`
  and `gpu_type`.
- `workload.pricing_mode` is `on_demand`, `spot`, or `cud_1yr`; unset defaults to
  spot for the `burst` archetype and on-demand otherwise. Spot/committed-use
  prices are used when a candidate carries `spot_price_hr` / `cud_1yr_price_hr`,
  else cost falls back to on-demand.
- Each result carries `contributions` (the exact `weight * sub-score` each
  component added to `score`) and `reason` (a one-line explanation of what drove
  the pick, including a spot/committed-use note).
- `workload.headroom` (default 0) asks for spare capacity above the declared
  vcpu/ram_gb, as a fraction (0.25 = 25% more, i.e. 1.25x). `workload.headroom_mode`
  is `hard` (raise the floor, so instances without the buffer are disqualified) or
  `soft` (prefer the buffer in scoring without disqualifying).
- Pass `candidates` in the request body to score your own catalog instead of
  the bundled snapshot (at most 10,000 per request; request bodies over 10 MB get 413).
- `workload.cpu_arch` (`x86_64` or `arm64`) is a hard floor for tools built for
  one CPU architecture, e.g. x86-only BCLConvert versus AWS Graviton instances.
- Scoring math: [cloudfit-core](https://github.com/cloudfit-io/cloudfit-core).
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Warm the snapshot cache once at startup so the first request is fast and a
    # missing/corrupt snapshot fails loudly here rather than on first request.
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

app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_body_bytes)
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
def root() -> dict[str, Any]:
    """Name, running version, snapshot size, and a pointer to these docs."""
    return {
        "name": settings.title,
        "version": settings.version,
        "instances": len(snapshot.all_instances()),
        "docs": "/docs",
    }


@app.get("/health", tags=["meta"], summary="Liveness probe")
def health() -> dict[str, str]:
    """Returns `{\"status\": \"ok\"}`. Use for container health checks."""
    return {"status": "ok"}
