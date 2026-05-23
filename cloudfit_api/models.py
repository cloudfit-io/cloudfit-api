"""Request/response models for the cloudfit-api endpoints.

Reuses cloudfit-core's WorkloadProfile, MachineType, and ScoredInstance directly
so the HTTP contract stays in lock-step with the scoring engine.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from cloudfit.models import MachineType, ScoredInstance, WorkloadProfile


class RecommendRequest(BaseModel):
    workload: WorkloadProfile
    region: str | None = Field(
        default=None, description="Restrict candidates to this region (snapshot default: all)."
    )
    top_k: int = Field(default=10, ge=1, le=100, description="Number of ranked results to return.")
    candidates: list[MachineType] | None = Field(
        default=None,
        description="Optional explicit candidate list. If omitted, the bundled snapshot is used.",
    )


class RecommendResponse(BaseModel):
    region: str | None
    total_candidates: int
    qualified: int
    disqualified: int
    results: list[ScoredInstance]


class InstancesResponse(BaseModel):
    count: int = Field(description="Total instances matching the filters (before limit).")
    region: str | None
    instances: list[MachineType]


class ProviderInfo(BaseModel):
    name: str
    instance_count: int
    regions: list[str]
    statuses: dict[str, int]


class ProvidersResponse(BaseModel):
    providers: list[ProviderInfo]


class DiffRequest(BaseModel):
    a: RecommendRequest
    b: RecommendRequest


class DiffSide(BaseModel):
    top: ScoredInstance | None
    qualified: int


class DiffDelta(BaseModel):
    instance_changed: bool
    price_hr_delta: float | None = None
    monthly_cost_delta: float | None = None  # price_hr_delta * 730
    vcpu_delta: int | None = None
    ram_gb_delta: float | None = None


class DiffResponse(BaseModel):
    a: DiffSide
    b: DiffSide
    delta: DiffDelta
