from fastapi.testclient import TestClient


def test_health_returns_200(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200


def test_health_body(client: TestClient) -> None:
    r = client.get("/health")
    body = r.json()
    assert body["status"] == "ok"
    assert body["db"] == "reachable"
