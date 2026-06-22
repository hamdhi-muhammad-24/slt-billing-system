from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# GET /customers
# ---------------------------------------------------------------------------

def test_list_customers_returns_200(client: TestClient) -> None:
    r = client.get("/customers")
    assert r.status_code == 200


def test_list_customers_pagination_envelope(client: TestClient) -> None:
    body = client.get("/customers").json()
    assert set(body.keys()) >= {"items", "total", "limit", "offset"}


def test_list_customers_total_is_8(client: TestClient) -> None:
    body = client.get("/customers").json()
    assert body["total"] == 8


def test_list_customers_default_pagination(client: TestClient) -> None:
    body = client.get("/customers").json()
    assert body["limit"] == 50
    assert body["offset"] == 0


# ---------------------------------------------------------------------------
# GET /accounts/1/invoices  — expects the 2024-01 invoice to be present
# ---------------------------------------------------------------------------

def _account1_invoice_2024_01(client: TestClient) -> dict:
    items = client.get("/accounts/1/invoices").json()["items"]
    inv = next((i for i in items if i["period"] == "2024-01"), None)
    assert inv is not None, "No 2024-01 invoice found for account 1"
    return inv


def test_account1_invoices_returns_200(client: TestClient) -> None:
    r = client.get("/accounts/1/invoices")
    assert r.status_code == 200


def test_account1_invoices_has_2024_01(client: TestClient) -> None:
    items = client.get("/accounts/1/invoices").json()["items"]
    periods = [i["period"] for i in items]
    assert "2024-01" in periods


def test_money_fields_are_strings(client: TestClient) -> None:
    inv = _account1_invoice_2024_01(client)
    for field in ("total_payable", "balance_bf", "payments_received",
                  "arrears", "charges_for_period"):
        value = inv[field]
        assert isinstance(value, str), (
            f"{field} must be a JSON string, got {type(value).__name__}: {value!r}"
        )


def test_2024_01_total_payable_exact(client: TestClient) -> None:
    inv = _account1_invoice_2024_01(client)
    assert inv["total_payable"] == "4628.52"
