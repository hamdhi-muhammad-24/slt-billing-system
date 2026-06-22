import pytest
from fastapi.testclient import TestClient

from app.api.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c
