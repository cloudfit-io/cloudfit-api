"""GET /instances: browse and filter the bundled snapshot."""

from __future__ import annotations

from fastapi import APIRouter, Query

from .. import snapshot
from ..models import InstancesResponse

router = APIRouter(tags=["instances"])


@router.get("/instances", response_model=InstancesResponse, summary="List instances")
def list_instances(
    provider: str | None = None,
    region: str | None = None,
    min_vcpu: int | None = Query(default=None, ge=1),
    min_ram_gb: float | None = Query(default=None, ge=0),
    gpu: bool | None = Query(default=None, description="True = GPU instances only, False = no GPU."),
    status: str | None = Query(default=None, description="active | deprecated | tombstoned"),
    limit: int = Query(default=100, ge=1, le=1000),
) -> InstancesResponse:
    """Filter the bundled snapshot. All filters are ANDed; omit a filter to skip it.

    `count` in the response is the total match across the snapshot; `instances` is
    the page (capped by `limit`). No pagination cursor yet: bump `limit` if you
    need more, up to 1000.
    """
    items = snapshot.filter_instances(
        provider=provider,
        region=region,
        min_vcpu=min_vcpu,
        min_ram_gb=min_ram_gb,
        gpu=gpu,
        status=status,
    )
    return InstancesResponse(count=len(items), region=region, instances=items[:limit])
