"""POST /recommend — rank machine types for a workload."""

from __future__ import annotations

from fastapi import APIRouter

from cloudfit import rank

from .. import snapshot
from ..models import RecommendRequest, RecommendResponse

router = APIRouter(tags=["recommend"])


@router.post("/recommend", response_model=RecommendResponse, summary="Rank machine types for a workload")
def recommend(req: RecommendRequest) -> RecommendResponse:
    """Score candidate instances against a workload profile and return the top picks.

    Candidates come from the request body if provided, otherwise from the bundled
    snapshot filtered by `region` and the workload's `providers` list. Hard floors
    (RAM / vCPU / GPU) are applied by cloudfit-core before scoring.
    """
    if req.candidates is not None:
        candidates = req.candidates
    else:
        candidates = snapshot.candidates_for(
            region=req.region, providers=req.workload.providers
        )

    results = rank(req.workload, candidates)
    qualified = [r for r in results if not r.disqualified]

    return RecommendResponse(
        region=req.region,
        total_candidates=len(candidates),
        qualified=len(qualified),
        disqualified=len(results) - len(qualified),
        results=qualified[: req.top_k],
    )
