"""Tests for POST /recommend."""


def _workload(**over):
    base = {"vcpu": 32, "ram_gb": 120, "workload": "io-intensive",
            "archetype": "io", "optimize_for": "balanced"}
    base.update(over)
    return base


def test_recommend_returns_ranked_results(client):
    r = client.post("/recommend", json={"workload": _workload(), "top_k": 5})
    assert r.status_code == 200
    body = r.json()
    assert body["qualified"] > 0
    assert len(body["results"]) <= 5
    scores = [x["score"] for x in body["results"]]
    assert scores == sorted(scores, reverse=True)


def test_recommend_respects_hard_floors(client):
    # every returned instance must meet the requested vCPU and RAM floors
    r = client.post("/recommend", json={"workload": _workload(vcpu=32, ram_gb=120), "top_k": 20})
    for item in r.json()["results"]:
        assert item["instance"]["vcpu"] >= 32
        assert item["instance"]["ram_gb"] >= 120


def test_recommend_all_modes_work(client):
    for mode in ("cost", "balanced", "performance", "availability"):
        r = client.post("/recommend", json={"workload": _workload(optimize_for=mode), "top_k": 5})
        assert r.status_code == 200, mode
        body = r.json()
        assert body["qualified"] > 0, mode
        scores = [x["score"] for x in body["results"]]
        assert scores == sorted(scores, reverse=True), mode


def test_recommend_top_k(client):
    r = client.post("/recommend", json={"workload": _workload(vcpu=2, ram_gb=8), "top_k": 3})
    assert len(r.json()["results"]) == 3


def test_recommend_gpu_requirement(client):
    payload = {"workload": _workload(vcpu=8, ram_gb=64, archetype="gpu",
                                     gpu={"required": True, "vram_gb": 40})}
    r = client.post("/recommend", json=payload)
    body = r.json()
    assert body["qualified"] > 0
    for item in body["results"]:
        assert item["instance"]["gpu_count"] >= 1


def test_recommend_with_explicit_candidates(client):
    payload = {
        "workload": _workload(vcpu=2, ram_gb=4),
        "candidates": [
            {"id": "tiny", "provider": "gcp", "vcpu": 2, "ram_gb": 8, "price_hr": 0.1},
            {"id": "big", "provider": "gcp", "vcpu": 8, "ram_gb": 32, "price_hr": 0.9},
        ],
    }
    r = client.post("/recommend", json=payload)
    body = r.json()
    assert body["total_candidates"] == 2
    assert {x["instance"]["id"] for x in body["results"]} <= {"tiny", "big"}


def test_recommend_unsatisfiable_returns_empty(client):
    r = client.post("/recommend", json={"workload": _workload(vcpu=100000, ram_gb=999999)})
    body = r.json()
    assert body["qualified"] == 0
    assert body["results"] == []
    assert body["disqualified"] > 0


def test_recommend_region_filter_restricts_results(client):
    """All results should be in the requested region when region is specified."""
    payload = {"workload": _workload(vcpu=4, ram_gb=16), "region": "asia-southeast1", "top_k": 10}
    r = client.post("/recommend", json=payload)
    body = r.json()
    assert body["region"] == "asia-southeast1"
    assert body["qualified"] > 0
    for item in body["results"]:
        assert item["instance"]["region"] == "asia-southeast1"


def test_recommend_region_in_workload_works_same_as_top_level(client):
    """Setting workload.region should have the same effect as top-level region."""
    payload = {
        "workload": _workload(vcpu=4, ram_gb=16, region="europe-west4"),
        "top_k": 5,
    }
    r = client.post("/recommend", json=payload)
    body = r.json()
    assert body["region"] == "europe-west4"
    for item in body["results"]:
        assert item["instance"]["region"] == "europe-west4"


def test_recommend_asymmetric_region_availability(client):
    """asia-southeast1 has fewer families than us-central1 in the bundled snapshot."""
    a = client.post("/recommend", json={
        "workload": _workload(vcpu=4, ram_gb=16),
        "region": "us-central1", "top_k": 100,
    }).json()
    b = client.post("/recommend", json={
        "workload": _workload(vcpu=4, ram_gb=16),
        "region": "asia-southeast1", "top_k": 100,
    }).json()
    # us-central1 has the full catalog; asia-southeast1 has only Tier 1 families
    assert a["total_candidates"] > b["total_candidates"]
