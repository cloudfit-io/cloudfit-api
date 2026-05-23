"""Shared test fixtures."""

import pytest
from fastapi.testclient import TestClient

from cloudfit_api.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
