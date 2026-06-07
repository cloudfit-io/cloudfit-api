# Changelog

All notable changes to `cloudfit-api` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - Unreleased

### Added
- Expose `workload.headroom` and `workload.headroom_mode` (from cloudfit-core 0.5.0). They ride inside the existing `workload` object, so there is no new endpoint or top-level field. `headroom` is a fraction (0.25 = 1.25x); `headroom_mode` is `hard` (raise the floor) or `soft` (prefer in scoring). The `POST /recommend` example and `/docs` notes now document them.

### Changed
- Require `cloudfit-core>=0.5.0`.

## [0.4.0] - 2026-06-02

### Changed
- Require `cloudfit-core>=0.4.0`: recommendations now use candidate-relative cost scoring and treat unpriced instances as cost 0.0 (not free).
- `/docs` description documents the cost normalization, unpriced behavior, and that `archetype` does not affect ranking.

## [0.3.0] - 2026-05-31

### Changed
- Bumped `cloudfit-core` dependency to `>=0.3.0,<0.4.0`. This picks up the new fit-based performance scoring: top picks now favor exact-fit instances rather than 2x-oversized ones, so `/recommend` returns substantively different (smaller, cheaper) recommendations for the same workload profile across all `optimize_for` modes. No HTTP API surface change.

## [0.2.0] - 2026-05-28

### Added
- Multi-region bundled snapshot. `data/gcp_snapshot.json` now contains 875 instance entries across five regions (`us-central1`, `us-east1`, `us-west1`, `europe-west4`, `asia-southeast1`) with realistic asymmetric availability and per-region price scaling.
- `POST /recommend` enforces a region hard floor when `region` is set, either at request top-level or inside `workload.region`. Top-level `region` takes precedence.
- `POST /diff` honors the same region precedence rules on both sides of the comparison.
- Three tests covering region behavior: region filter restricts results, `workload.region` matches top-level `region`, and asymmetric availability is reflected in candidate counts.
- OpenAPI example for `/recommend` now includes a `region` value so it surfaces in Swagger UI.

### Changed
- Dependency on `cloudfit-core` bumped to `>=0.2.0` (region field requires the new core).
- `cloudfit_api/snapshot.py` documentation noting the multi-region snapshot shape.
- README "About the snapshot" section updated to describe the five-region shape, asymmetric availability tiers, and per-region price multipliers.

## [0.1.0] - 2026-05-23

### Added
- Initial release of the cloudfit FastAPI service.
- `POST /recommend` to rank machine types against a workload profile.
- `GET /instances` to browse and filter the bundled snapshot.
- `GET /providers` to summarize providers, regions, and statuses.
- `POST /diff` to compare top picks for two workloads.
- `GET /` and `GET /health` for service metadata and health check.
- Bundled GCP snapshot (267 instances, `us-central1` only).
- Dockerfile honoring `$PORT` for Cloud Run / Hugging Face Spaces deployment.
- Hugging Face Spaces front-matter (`sdk: docker`, `app_port: 8080`).
- `CLOUDFIT_SNAPSHOT_PATH` and `CLOUDFIT_CORS_ORIGINS` environment configuration.
- OpenAPI documentation served at `/docs` with worked examples for every endpoint.
- Apache 2.0 license. CITATION.cff for academic citation.

[0.3.0]: https://github.com/cloudfit-io/cloudfit-api/releases/tag/v0.3.0
[0.2.0]: https://github.com/cloudfit-io/cloudfit-api/releases/tag/v0.2.0
[0.1.0]: https://github.com/cloudfit-io/cloudfit-api/releases/tag/v0.1.0
