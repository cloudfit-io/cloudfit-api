"""POST /recommend: rank machine types for a workload."""

from __future__ import annotations

from fastapi import APIRouter

from cloudfit import rank

from .. import snapshot
from ..models import RecommendRequest, RecommendResponse

router = APIRouter(tags=["recommend"])


@router.post("/recommend", response_model=RecommendResponse, summary="Recommend machine types")
def recommend(req: RecommendRequest) -> RecommendResponse:
    """Rank instances and return the top `top_k`.

    **Candidates.** Defaults to the bundled snapshot, filtered by `region` and the
    workload's `providers` list. Pass `candidates` to score your own catalog.

    **Region.** Top-level `region` wins over `workload.region`. When set, instances
    in other regions are disqualified by the hard floor.

    **Hard floors.** Region, RAM, vCPU, and GPU mismatches disqualify candidates
    before scoring. Counts surface in the response (`qualified`, `disqualified`).
    """
    # Request-level region takes precedence; fall back to workload.region.
    effective_region = req.region or req.workload.region

    if req.candidates is not None:
        candidates = req.candidates
    else:
        candidates = snapshot.candidates_for(
            region=effective_region, providers=req.workload.providers
        )

    # Copy region into the workload so the core hard floor enforces it too.
    # This matters for caller-provided candidate lists that span regions.
    workload = req.workload.model_copy(update={"region": effective_region}) if effective_region else req.workload

    results = rank(workload, candidates)
    qualified = [r for r in results if not r.disqualified]

    return RecommendResponse(
        region=effective_region,
        total_candidates=len(candidates),
        qualified=len(qualified),
        disqualified=len(results) - len(qualified),
        results=qualified[: req.top_k],
    )
