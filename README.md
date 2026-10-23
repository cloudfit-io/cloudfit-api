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

[![Release](https://img.shields.io/github/v/release/cloudfit-io/cloudfit-api)](https://github.com/cloudfit-io/cloudfit-api/releases)
[![CI](https://github.com/cloudfit-io/cloudfit-api/actions/workflows/ci.yml/badge.svg)](https://github.com/cloudfit-io/cloudfit-api/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)

**HTTP API over [cloudfit-core](https://github.com/cloudfit-io/cloudfit-core).** A thin, stateless FastAPI service that scores cloud machine types against a workload profile.

It ships with a **bundled GCP machine-type snapshot**, so it runs out of the box: no database, no cloud credentials, no provider calls at request time. The snapshot's prices are refreshed weekly by an automated pull request, and you can point the service at your own snapshot whenever you like.

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

Each result includes the instance, `score`, the `cost_score` / `perf_score` / `avail_score` sub-scores, `contributions` (exactly what each term added to `score`), and a one-line `reason`, for example:

```json
"reason": "Led by cost; c3 cores ~20% faster than baseline; priced on spot (interruptible)."
```

### Pricing modes

`workload.pricing_mode` picks the price the cost score uses: `on_demand`, `spot`, or `cud_1yr` (1-year committed use). Left unset, the `burst` archetype uses spot and everything else on-demand. Instances without a price for the chosen mode fall back to on-demand.

```bash
curl -s http://127.0.0.1:8000/recommend -H 'content-type: application/json' -d '{
  "workload": {"vcpu": 16, "ram_gb": 64, "archetype": "cpu", "optimize_for": "cost", "pricing_mode": "spot"},
  "top_k": 3
}'
```

### Region-aware recommend

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

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check cloudfit_api/ && mypy --strict cloudfit_api/
```

CI runs the same checks on Python 3.10 to 3.12 for every pull request.

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

`data/gcp_snapshot.json` is a **representative sample** of GCP Compute Engine machine types across **five regions** (`us-central1`, `us-east1`, `us-west1`, `europe-west4`, `asia-southeast1`). 875 entries total, with realistic asymmetric availability: us-central1 carries the full catalog, asia-southeast1 carries only the Tier 1 families that have rolled out everywhere. Every entry has a `perf_factor`, and GPU entries a `gpu_type`.

**Prices are refreshed weekly.** [`cloudfit-provider-gcp`](https://github.com/cloudfit-io/cloudfit-provider-gcp)'s scheduled workflow pulls on-demand, spot, and 1-year committed-use prices for CPU/RAM machine types from the live GCP billing catalog and opens a pull request here; CI runs the test suite on it, and merging redeploys the live demo. GPU instances keep approximate on-demand prices and have no spot or committed-use price.

The machine-type list itself is a curated sample, not an exhaustive catalog. Build your own with `cloudfit-provider-gcp` and point `CLOUDFIT_SNAPSHOT_PATH` at it, or supply your own `candidates` directly in the `/recommend` request body.

> Stateless by design: a registry-backed, multi-provider deployment is a later step. This service is the thin scoring layer.

---

## Ecosystem

- [`cloudfit-core`](https://github.com/cloudfit-io/cloudfit-core): scoring engine
- [`cloudfit-provider-gcp`](https://github.com/cloudfit-io/cloudfit-provider-gcp): GCP machine-type fetcher
- [`cloudfit-ui`](https://github.com/cloudfit-io/cloudfit-ui): Gradio demo over the same scoring engine ([live demo](https://chaitanyakasaraneni-cloudfit-ui.hf.space)). Use this if you would rather fill a form than write JSON.

## License

Apache 2.0: see [LICENSE](LICENSE).
