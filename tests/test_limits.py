"""Tests for request-size limits and the cpu_arch floor over HTTP."""

from cloudfit_api.config import settings
from cloudfit_api.models import MAX_CANDIDATES


def _candidate(i):
    return {"id": f"x-{i}", "provider": "gcp", "vcpu": 8, "ram_gb": 32, "price_hr": 1.0}


def test_declared_oversize_body_gets_413(client):
    big = "x" * (settings.max_body_bytes + 1)
    r = client.post("/recommend", content=big, headers={"content-type": "application/json"})
    assert r.status_code == 413
    assert "limit" in r.json()["detail"]


def test_streamed_oversize_body_gets_413(client):
    def chunks():
        yield b'{"workload": {"vcpu": 8, "ram_gb": 32}, "pad": "'
        for _ in range(11):
            yield b"x" * 1_000_000
        yield b'"}'

    r = client.post("/recommend", content=chunks(), headers={"content-type": "application/json"})
    assert r.status_code == 413


def test_too_many_candidates_is_rejected(client):
    payload = {"workload": {"vcpu": 8, "ram_gb": 32},
               "candidates": [_candidate(i) for i in range(MAX_CANDIDATES + 1)]}
    r = client.post("/recommend", json=payload)
    assert r.status_code == 422


def test_cpu_arch_floor_over_http(client):
    body = client.post("/recommend", json={
        "workload": {"vcpu": 16, "ram_gb": 64, "cpu_arch": "x86_64", "providers": ["aws"]},
        "region": "us-east-1", "top_k": 20,
    }).json()
    ids = [r["instance"]["id"] for r in body["results"]]
    assert ids
    assert not any(i.split(".")[0].endswith(("g", "gd", "gn")) for i in ids)
