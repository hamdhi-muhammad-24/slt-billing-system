from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# POST /billing/generate-one: duplicate guard (account 1, billing month 2024-02 is GENERATED)
# ---------------------------------------------------------------------------

def test_generate_one_409_for_already_generated(client: TestClient) -> None:
    r = client.post(
        "/billing/generate-one",
        json={"account_id": 1, "period": "2024-02"},
    )
    assert r.status_code == 409


def test_generate_one_409_body_has_detail(client: TestClient) -> None:
    r = client.post(
        "/billing/generate-one",
        json={"account_id": 1, "period": "2024-02"},
    )
    assert "detail" in r.json()


# ---------------------------------------------------------------------------
# POST /billing/generate-one — 404 for a period that has no invoice in the DB
# ---------------------------------------------------------------------------

def test_generate_one_404_for_nonexistent_period(client: TestClient) -> None:
    r = client.post(
        "/billing/generate-one",
        json={"account_id": 1, "period": "2022-06"},
    )
    assert r.status_code == 404


def test_generate_one_404_body_has_detail(client: TestClient) -> None:
    r = client.post(
        "/billing/generate-one",
        json={"account_id": 1, "period": "2022-06"},
    )
    assert "detail" in r.json()


# ---------------------------------------------------------------------------
# GET /invoices/1 — read back confirms the 2024-01 total_payable
# ---------------------------------------------------------------------------

def test_invoice_1_total_payable_exact(client: TestClient) -> None:
    r = client.get("/invoices/1")
    assert r.status_code == 200
    assert r.json()["total_payable"] == "4628.52"


def test_invoice_1_total_payable_is_string(client: TestClient) -> None:
    r = client.get("/invoices/1")
    assert isinstance(r.json()["total_payable"], str)
