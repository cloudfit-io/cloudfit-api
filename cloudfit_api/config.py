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
    CLOUDFIT_SNAPSHOT_PATH  path to the bundled machine-type snapshot JSON
    CLOUDFIT_CORS_ORIGINS   comma-separated allowed origins (default "*")
    """

    def __init__(self) -> None:
        self.title = "cloudfit-api"
        self.version = __version__
        self.description = (
            "Stateless HTTP API over cloudfit-core. Scores cloud machine types "
            "against a workload profile using a bundled provider snapshot."
        )
        self.snapshot_path = Path(
            os.getenv("CLOUDFIT_SNAPSHOT_PATH", str(_REPO_ROOT / "data" / "gcp_snapshot.json"))
        )
        origins = os.getenv("CLOUDFIT_CORS_ORIGINS", "*").strip()
        self.cors_origins = [o.strip() for o in origins.split(",")] if origins else ["*"]


settings = Settings()
