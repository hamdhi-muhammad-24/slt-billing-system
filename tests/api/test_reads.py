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


def test_list_customers_total_has_realistic_seed_set(client: TestClient) -> None:
    body = client.get("/customers").json()
    assert body["total"] >= 28


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


def test_customer_profile_includes_kyc_contact_fields(client: TestClient) -> None:
    customer = client.get("/customers/1").json()
    assert customer["nic"]
    assert customer["email"]
    assert customer["phone"]


def test_account_usage_history_returns_six_months(client: TestClient) -> None:
    body = client.get("/accounts/1/usage/history?months=6").json()
    periods = {row["period"] for row in body}
    assert {"2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"} <= periods


def test_daily_usage_endpoint_returns_rows(client: TestClient) -> None:
    services = client.get("/accounts/1/service-accounts").json()
    broadband = next(s for s in services if s["service_type"] == "BROADBAND")
    rows = client.get(f"/service-accounts/{broadband['id']}/daily-usage?period=2026-06").json()
    assert len(rows) >= 28
    assert {"usage_date", "download_gb", "upload_gb", "total_gb"} <= set(rows[0])


def test_admin_dashboard_summary_returns_operational_counts(client: TestClient) -> None:
    body = client.get("/billing/admin-summary").json()
    assert body["total_customers"] >= 28
    assert body["active_accounts"] >= 1
    assert body["generated_invoices"] >= 1
    assert "recent_billing_runs" in body
    assert "recent_invoices" in body
    assert "alerts" in body
