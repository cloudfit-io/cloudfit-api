"""Validation, flat-body, and snapshot-loading tests."""

import pytest

from cloudfit_api import snapshot
from cloudfit_api.config import settings


def test_missing_vcpu_returns_422(client):
    r = client.post("/recommend", json={"workload": {"ram_gb": 128}})
    assert r.status_code == 422


def test_vcpu_zero_returns_422(client):
    r = client.post("/recommend", json={"workload": {"vcpu": 0, "ram_gb": 128}})
    assert r.status_code == 422


def test_empty_body_returns_422(client):
    r = client.post("/recommend", json={})
    assert r.status_code == 422


def test_unknown_workload_field_returns_422(client):
    r = client.post("/recommend", json={"workload": {"vcpu": 8, "ram_gb": 32, "typo": "x"}})
    assert r.status_code == 422


def test_flat_workload_body_is_accepted(client):
    # No "workload" wrapper — fields are at the top level.
    r = client.post(
        "/recommend",
        json={"vcpu": 32, "ram_gb": 128, "archetype": "cpu", "optimize_for": "balanced"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["qualified"] > 0
    assert len(body["results"]) >= 1


def test_flat_body_keeps_reserved_keys(client):
    r = client.post(
        "/recommend",
        json={"vcpu": 4, "ram_gb": 16, "region": "asia-southeast1", "top_k": 3},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["region"] == "asia-southeast1"
    assert len(body["results"]) <= 3


def test_snapshot_loads_nonempty_on_startup(client):
    # The client fixture's lifespan warms the snapshot; it must be non-empty.
    assert len(snapshot.load_snapshot()) > 0
    assert client.get("/").json()["instances"] == len(snapshot.load_snapshot())


def test_missing_snapshot_raises_clear_error(monkeypatch, tmp_path):
    snapshot.load_snapshot.cache_clear()
    monkeypatch.setattr(settings, "snapshot_path", tmp_path / "does_not_exist.json")
    try:
        with pytest.raises(RuntimeError, match="Snapshot file not found"):
            snapshot.load_snapshot()
    finally:
        snapshot.load_snapshot.cache_clear()
