"""Tests for POST /diff."""


def _req(**over):
    wl = {"vcpu": 32, "ram_gb": 120, "archetype": "io", "optimize_for": "balanced"}
    wl.update(over.pop("workload", {}))
    return {"workload": wl, **over}


def test_diff_two_workloads(client):
    payload = {
        "a": _req(workload={"vcpu": 16, "ram_gb": 64}),
        "b": _req(workload={"vcpu": 64, "ram_gb": 256}),
    }
    r = client.post("/diff", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["a"]["top"] is not None
    assert body["b"]["top"] is not None
    # the bigger workload should pick a different (larger) instance
    assert body["delta"]["instance_changed"] is True
    assert body["delta"]["vcpu_delta"] >= 0


def test_diff_reports_cost_delta(client):
    payload = {
        "a": _req(workload={"vcpu": 8, "ram_gb": 32}),
        "b": _req(workload={"vcpu": 8, "ram_gb": 32}),
    }
    body = client.post("/diff", json=payload).json()
    # identical workloads -> same pick -> zero deltas
    assert body["delta"]["instance_changed"] is False
    assert body["delta"]["price_hr_delta"] == 0
    assert body["delta"]["monthly_cost_delta"] == 0


def test_diff_handles_unsatisfiable_side(client):
    payload = {
        "a": _req(workload={"vcpu": 8, "ram_gb": 32}),
        "b": _req(workload={"vcpu": 999999, "ram_gb": 999999}),
    }
    body = client.post("/diff", json=payload).json()
    assert body["a"]["top"] is not None
    assert body["b"]["top"] is None
    assert body["b"]["qualified"] == 0
