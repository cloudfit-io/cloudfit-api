"""Loads and queries the bundled machine-type snapshot.

The snapshot is a static JSON file of normalized `MachineType` records (the same
shape cloudfit providers emit). It is loaded once and cached. This is what makes
the API stateless: no database, no live cloud calls, no credentials.
"""

from __future__ import annotations

import json
from functools import lru_cache

from cloudfit.models import MachineType

from .config import settings


@lru_cache(maxsize=1)
def load_snapshot() -> list[MachineType]:
    """Load the snapshot JSON into MachineType objects (cached for the process)."""
    raw = json.loads(settings.snapshot_path.read_text())
    return [MachineType(**row) for row in raw]


def all_instances() -> list[MachineType]:
    """Return every instance in the snapshot."""
    return load_snapshot()


def filter_instances(
    *,
    provider: str | None = None,
    region: str | None = None,
    min_vcpu: int | None = None,
    min_ram_gb: float | None = None,
    gpu: bool | None = None,
    status: str | None = None,
) -> list[MachineType]:
    """Return snapshot instances matching all given filters."""
    items = load_snapshot()
    if provider is not None:
        items = [m for m in items if m.provider == provider]
    if region is not None:
        items = [m for m in items if m.region == region]
    if min_vcpu is not None:
        items = [m for m in items if m.vcpu >= min_vcpu]
    if min_ram_gb is not None:
        items = [m for m in items if m.ram_gb >= min_ram_gb]
    if gpu is not None:
        items = [m for m in items if (m.gpu_count > 0) is gpu]
    if status is not None:
        items = [m for m in items if m.status == status]
    return items


def candidates_for(
    region: str | None = None,
    providers: list[str] | None = None,
) -> list[MachineType]:
    """Candidate set for scoring: snapshot filtered by region and provider list."""
    items = filter_instances(region=region)
    if providers:
        items = [m for m in items if m.provider in providers]
    return items
