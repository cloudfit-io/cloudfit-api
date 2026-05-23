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

```jsonc
{
  "region": null,
  "total_candidates": 267,
  "qualified": 110,
  "disqualified": 157,
  "results": [
    {"instance": {"id": "n2d-standard-64", "vcpu": 64, "ram_gb": 256.0, "price_hr": 2.7037,
                  "status": "active", "generation": "second", "...": "..."},
     "score": 0.9745, "cost_score": 0.9228, "perf_score": 1.0, "avail_score": 1.0,
     "disqualified": false}
  ]
}
```

### Browse instances

```bash
curl 'http://127.0.0.1:8000/instances?min_vcpu=64&gpu=false&limit=5'
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

`data/gcp_snapshot.json` is a **representative sample** of GCP Compute Engine machine types (normalized to the cloudfit `MachineType` schema) — not a live or exhaustive list. Regenerate it from live data with [`cloudfit-provider-gcp`](https://github.com/cloudfit-io/cloudfit-provider-gcp) and point `CLOUDFIT_SNAPSHOT_PATH` at the result, or supply your own `candidates` directly in the `/recommend` request body.

> Stateless by design: the registry + Redis-cached, multi-provider deployment described in the cloudfit architecture is a later step. This service is the thin scoring layer.

---

## Ecosystem

- [`cloudfit-core`](https://github.com/cloudfit-io/cloudfit-core) — scoring engine
- [`cloudfit-provider-gcp`](https://github.com/cloudfit-io/cloudfit-provider-gcp) — GCP machine-type fetcher

## License

Apache 2.0 — see [LICENSE](LICENSE).
