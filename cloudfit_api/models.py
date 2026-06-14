"""Request/response models for the cloudfit-api endpoints.

Reuses cloudfit-core's WorkloadProfile, MachineType, and ScoredInstance directly
so the HTTP contract stays in lock-step with the scoring engine.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator

from cloudfit.models import MachineType, ScoredInstance, WorkloadProfile

_REQUEST_RESERVED_KEYS = {"workload", "region", "top_k", "candidates"}


class RecommendRequest(BaseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "workload": {
                        "vcpu": 32,
                        "ram_gb": 120,
                        "archetype": "io",
                        "optimize_for": "balanced",
                        "headroom": 0.15,
                        "headroom_mode": "hard",
                    },
                    "region": "us-central1",
                    "top_k": 3,
                }
            ]
        }
    }

    @model_validator(mode="before")
    @classmethod
    def _accept_flat_workload(cls, data: Any) -> Any:
        """Accept a flat workload body as a convenience.

        A request carrying workload fields at the top level (e.g.
        ``{"vcpu": 32, "ram_gb": 128}``) is rewrapped as ``{"workload": {...}}``.
        Reserved request keys (region, top_k, candidates) stay at the top level.
        Already-nested requests pass through unchanged.
        """
        if isinstance(data, dict) and "workload" not in data:
            workload_fields = {
                k: v for k, v in data.items() if k not in _REQUEST_RESERVED_KEYS
            }
            if workload_fields:
                rest = {k: v for k, v in data.items() if k in _REQUEST_RESERVED_KEYS}
                return {"workload": workload_fields, **rest}
        return data

    workload: WorkloadProfile
    region: str | None = Field(
        default=None,
        description="Restrict candidates to this region. Bundled snapshot regions: us-central1, us-east1, us-west1, europe-west4, asia-southeast1. Top-level `region` overrides `workload.region`.",
    )
    top_k: int = Field(default=10, ge=1, le=100, description="Number of ranked results to return.")
    candidates: list[MachineType] | None = Field(
        default=None,
        description="Optional explicit candidate list. If omitted, the bundled snapshot is used.",
    )


class RecommendResponse(BaseModel):
    region: str | None = Field(description="Effective region used (request-level overrides workload-level).")
    total_candidates: int = Field(description="Size of the candidate set scored.")
    qualified: int = Field(description="Candidates that passed all hard floors.")
    disqualified: int = Field(description="Candidates that failed at least one hard floor.")
    results: list[ScoredInstance] = Field(description="Top picks, sorted by composite score descending. Length <= top_k.")


class InstancesResponse(BaseModel):
    count: int = Field(description="Total instances matching the filters (before limit).")
    region: str | None = Field(description="Region filter applied (echoed for convenience).")
    instances: list[MachineType] = Field(description="Page of matching instances, capped by limit.")


class ProviderInfo(BaseModel):
    name: str = Field(description="Provider identifier (e.g. gcp, aws).")
    instance_count: int = Field(description="Total instances from this provider in the snapshot.")
    regions: list[str] = Field(description="Distinct regions this provider serves in the snapshot.")
    statuses: dict[str, int] = Field(description="Count by status: active, deprecated, tombstoned.")


class ProvidersResponse(BaseModel):
    providers: list[ProviderInfo]


class DiffRequest(BaseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "a": {"workload": {"vcpu": 16, "ram_gb": 64, "archetype": "io"}},
                    "b": {"workload": {"vcpu": 64, "ram_gb": 256, "archetype": "io"}},
                }
            ]
        }
    }

    a: RecommendRequest = Field(description="Baseline workload (the 'before').")
    b: RecommendRequest = Field(description="Comparison workload (the 'after'). Delta is computed as b - a.")


class DiffSide(BaseModel):
    top: ScoredInstance | None = Field(description="Top pick for this side, or null if nothing qualified.")
    qualified: int = Field(description="Number of instances that passed hard floors on this side.")


class DiffDelta(BaseModel):
    instance_changed: bool = Field(description="True if the top pick id differs between sides.")
    price_hr_delta: float | None = Field(default=None, description="b.price_hr - a.price_hr. Positive means b is more expensive.")
    monthly_cost_delta: float | None = Field(default=None, description="price_hr_delta * 730 (standard hours-per-month convention).")
    vcpu_delta: int | None = Field(default=None, description="b.vcpu - a.vcpu.")
    ram_gb_delta: float | None = Field(default=None, description="b.ram_gb - a.ram_gb.")


class DiffResponse(BaseModel):
    a: DiffSide
    b: DiffSide
    delta: DiffDelta
