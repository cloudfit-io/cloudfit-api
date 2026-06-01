"""GET /providers: summarize the providers present in the snapshot."""

from __future__ import annotations

from collections import Counter, defaultdict

from fastapi import APIRouter

from cloudfit.models import MachineType

from .. import snapshot
from ..models import ProviderInfo, ProvidersResponse

router = APIRouter(tags=["providers"])


@router.get("/providers", response_model=ProvidersResponse, summary="Per-provider summary")
def list_providers() -> ProvidersResponse:
    """For each provider in the snapshot: total instance count, the regions present,
    and a breakdown by status (`active`, `deprecated`, `tombstoned`). Useful for
    confirming a deploy is wired to the snapshot you expect."""
    by_provider: dict[str, list[MachineType]] = defaultdict(list)
    for m in snapshot.all_instances():
        by_provider[m.provider].append(m)

    infos = [
        ProviderInfo(
            name=name,
            instance_count=len(items),
            regions=sorted({m.region for m in items}),
            statuses=dict(Counter(m.status for m in items)),
        )
        for name, items in sorted(by_provider.items())
    ]
    return ProvidersResponse(providers=infos)
