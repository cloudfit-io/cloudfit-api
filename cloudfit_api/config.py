"""Runtime settings, read from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from . import __version__

# cloudfit_api/  ->  repo root (parent of the package dir)
_PKG_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PKG_DIR.parent


class Settings:
    """Process settings sourced from env vars (with sensible defaults).

    Env vars
    --------
    CLOUDFIT_SNAPSHOT_PATH  comma-separated paths to machine-type snapshot JSON files
                            (default: the bundled GCP and AWS snapshots)
    CLOUDFIT_CORS_ORIGINS   comma-separated allowed origins (default "*")
    """

    def __init__(self) -> None:
        self.title = "cloudfit-api"
        self.version = __version__
        self.description = (
            "Stateless HTTP API over cloudfit-core. Scores cloud machine types "
            "against a workload profile using bundled provider snapshots."
        )
        default_paths = ",".join(
            str(_REPO_ROOT / "data" / name) for name in ("gcp_snapshot.json", "aws_snapshot.json")
        )
        self.snapshot_paths = [
            Path(p.strip())
            for p in os.getenv("CLOUDFIT_SNAPSHOT_PATH", default_paths).split(",")
            if p.strip()
        ]
        origins = os.getenv("CLOUDFIT_CORS_ORIGINS", "*").strip()
        self.cors_origins = [o.strip() for o in origins.split(",")] if origins else ["*"]


settings = Settings()
