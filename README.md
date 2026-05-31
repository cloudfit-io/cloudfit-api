---
title: cloudfit-api
emoji: 🖥️
colorFrom: green
colorTo: blue
sdk: docker
app_port: 8080
pinned: false
license: apache-2.0
---

# cloudfit-api

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)

**HTTP API over [cloudfit-core](https://github.com/cloudfit-io/cloudfit-core).** A thin, stateless FastAPI service that scores cloud machine types against a workload profile.

It ships with a **bundled GCP machine-type snapshot**, so it runs out of the box — no database, no cloud credentials, no provider calls at request time. Point it at a fresher snapshot whenever you like.

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/recommend` | Rank machine types for a workload profile |
| `GET`  | `/instances` | Browse / filter the snapshot |
| `GET`  | `/providers` | Per-provider counts, regions, status breakdown |
| `POST` | `/diff` | Compare the top recommendation for two workloads |
| `GET`  | `/` , `/health` | Service metadata and health check |

Interactive OpenAPI docs are served at **`/docs`**.

---

## Quick start

```bash
pip install -e ".[dev]"          # needs cloudfit-core (on PyPI) + fastapi
uvicorn cloudfit_api.main:app --reload
# open http://127.0.0.1:8000/docs
```

(or `make run`)

### Recommend

```bash
curl -s http://127.0.0.1:8000/recommend -H 'content-type: application/json' -d '{
  "workload": {"vcpu": 32, "ram_gb": 120, "archetype": "io", "optimize_for": "balanced"},
  "top_k": 3
}'
```

### Region-aware recommend (new in 0.2)

Restrict candidates to a specific GCP region. The hard floor disqualifies anything not available there.

```bash
# us-central1 has the full catalog
curl -s http://127.0.0.1:8000/recommend -H 'content-type: application/json' -d '{
  "workload": {"vcpu": 16, "ram_gb": 64, "optimize_for": "balanced"},
  "region": "us-central1",
  "top_k": 5
}'

# asia-southeast1 has only Tier 1 families (e2, n1, n2, c2) in the bundled snapshot
curl -s http://127.0.0.1:8000/recommend -H 'content-type: application/json' -d '{
  "workload": {"vcpu": 16, "ram_gb": 64, "optimize_for": "balanced"},
  "region": "asia-southeast1",
  "top_k": 5
}'
```

`region` can also be set inside the `workload` object. Top-level `region` takes precedence when both are present.

### Browse instances

```bash
curl 'http://127.0.0.1:8000/instances?region=europe-west4&min_vcpu=64&limit=5'
curl 'http://127.0.0.1:8000/instances?gpu=true'
curl 'http://127.0.0.1:8000/providers'
```

### Diff two workloads (migration planning)

```bash
curl -s http://127.0.0.1:8000/diff -H 'content-type: application/json' -d '{
  "a": {"workload": {"vcpu": 16, "ram_gb": 64}},
  "b": {"workload": {"vcpu": 64, "ram_gb": 256}}
}'
```

Returns the top pick for each workload plus the delta (instance change, price/hr, monthly cost, vCPU, RAM).

---

## Docker

```bash
docker build -t cloudfit-api .
docker run -p 8080:8080 cloudfit-api
# http://127.0.0.1:8080/docs
```

The image honors `$PORT` (Cloud Run sets it automatically) and bundles the snapshot at `/app/data`.

---

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `CLOUDFIT_SNAPSHOT_PATH` | `data/gcp_snapshot.json` | Path to the machine-type snapshot |
| `CLOUDFIT_CORS_ORIGINS` | `*` | Comma-separated allowed origins |

---

## About the snapshot

`data/gcp_snapshot.json` is a **representative sample** of GCP Compute Engine machine types across **five regions** (`us-central1`, `us-east1`, `us-west1`, `europe-west4`, `asia-southeast1`). 875 entries total, with realistic asymmetric availability: us-central1 carries the full catalog, asia-southeast1 carries only the Tier 1 families that have rolled out everywhere. Prices are adjusted with approximate per-region multipliers.

This is a representative sample, not a live or exhaustive list. Regenerate it from live data with [`cloudfit-provider-gcp`](https://github.com/cloudfit-io/cloudfit-provider-gcp) and point `CLOUDFIT_SNAPSHOT_PATH` at the result, or supply your own `candidates` directly in the `/recommend` request body.

> Stateless by design: the registry + Redis-cached, multi-provider deployment described in the cloudfit architecture is a later step. This service is the thin scoring layer.

---

## Ecosystem

- [`cloudfit-core`](https://github.com/cloudfit-io/cloudfit-core) — scoring engine
- [`cloudfit-provider-gcp`](https://github.com/cloudfit-io/cloudfit-provider-gcp) — GCP machine-type fetcher
- [`cloudfit-ui`](https://github.com/cloudfit-io/cloudfit-ui) — Gradio demo over the same scoring engine ([live demo](https://chaitanyakasaraneni-cloudfit-ui.hf.space)). Use this if you would rather fill a form than write JSON.

## License

Apache 2.0 — see [LICENSE](LICENSE).
