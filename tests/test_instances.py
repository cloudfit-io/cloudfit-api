"""Tests for GET /instances and GET /providers."""


def test_root_and_health(client):
    assert client.get("/health").json() == {"status": "ok"}
    root = client.get("/").json()
    assert root["instances"] > 0


def test_instances_returns_data(client):
    r = client.get("/instances")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] > 0
    assert len(body["instances"]) <= 100  # default limit


def test_instances_min_vcpu_filter(client):
    r = client.get("/instances", params={"min_vcpu": 64, "limit": 1000})
    assert all(m["vcpu"] >= 64 for m in r.json()["instances"])


def test_instances_gpu_filter(client):
    only_gpu = client.get("/instances", params={"gpu": True, "limit": 1000}).json()["instances"]
    assert only_gpu and all(m["gpu_count"] >= 1 for m in only_gpu)
    no_gpu = client.get("/instances", params={"gpu": False, "limit": 1000}).json()["instances"]
    assert all(m["gpu_count"] == 0 for m in no_gpu)


def test_instances_status_filter(client):
    r = client.get("/instances", params={"status": "tombstoned", "limit": 1000})
    insts = r.json()["instances"]
    assert insts and all(m["status"] == "tombstoned" for m in insts)


def test_instances_limit(client):
    r = client.get("/instances", params={"limit": 5})
    body = r.json()
    assert len(body["instances"]) == 5
    assert body["count"] >= 5  # count reflects total matches, not the page


def test_instances_unknown_region_is_empty(client):
    r = client.get("/instances", params={"region": "nowhere-1"})
    assert r.json()["count"] == 0


def test_providers_summary(client):
    body = client.get("/providers").json()
    assert body["providers"]
    gcp = next(p for p in body["providers"] if p["name"] == "gcp")
    assert gcp["instance_count"] > 0
    assert "us-central1" in gcp["regions"]
    assert "active" in gcp["statuses"]
