"""POST /diff — compare the top recommendation for two workload profiles."""

from __future__ import annotations

from fastapi import APIRouter

from cloudfit import rank

from .. import snapshot
from ..models import (
    DiffDelta,
    DiffRequest,
    DiffResponse,
    DiffSide,
    RecommendRequest,
)

router = APIRouter(tags=["diff"])

_HOURS_PER_MONTH = 730


def _recommend_one(req: RecommendRequest) -> list:
    if req.candidates is not None:
        candidates = req.candidates
    else:
        candidates = snapshot.candidates_for(
            region=req.region, providers=req.workload.providers
        )
    results = rank(req.workload, candidates)
    return [r for r in results if not r.disqualified]


@router.post("/diff", response_model=DiffResponse, summary="Compare two workloads")
def diff(req: DiffRequest) -> DiffResponse:
    """Recommend for two workloads and report the delta between the top picks.

    Useful for migration planning — e.g. comparing the recommendation for an old
    workload profile against a new one and seeing the cost/spec impact.
    """
    qa = _recommend_one(req.a)
    qb = _recommend_one(req.b)
    top_a = qa[0] if qa else None
    top_b = qb[0] if qb else None

    if top_a is not None and top_b is not None:
        ia, ib = top_a.instance, top_b.instance
        price_delta = round(ib.price_hr - ia.price_hr, 4)
        delta = DiffDelta(
            instance_changed=ia.id != ib.id,
            price_hr_delta=price_delta,
            monthly_cost_delta=round(price_delta * _HOURS_PER_MONTH, 2),
            vcpu_delta=ib.vcpu - ia.vcpu,
            ram_gb_delta=round(ib.ram_gb - ia.ram_gb, 1),
        )
    else:
        delta = DiffDelta(instance_changed=top_a is not top_b)

    return DiffResponse(
        a=DiffSide(top=top_a, qualified=len(qa)),
        b=DiffSide(top=top_b, qualified=len(qb)),
        delta=delta,
    )
