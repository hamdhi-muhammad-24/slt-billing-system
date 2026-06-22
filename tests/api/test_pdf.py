from fastapi.testclient import TestClient


def test_invoice_1_pdf_returns_200(client: TestClient) -> None:
    r = client.get("/invoices/1/pdf")
    assert r.status_code == 200


def test_invoice_1_pdf_content_type(client: TestClient) -> None:
    r = client.get("/invoices/1/pdf")
    assert "application/pdf" in r.headers["content-type"]


def test_invoice_1_pdf_content_disposition(client: TestClient) -> None:
    r = client.get("/invoices/1/pdf")
    assert r.headers["content-disposition"] == 'attachment; filename="invoice-1.pdf"'


def test_invoice_1_pdf_magic_bytes(client: TestClient) -> None:
    r = client.get("/invoices/1/pdf")
    assert r.content[:4] == b"%PDF"


def test_invoice_1_pdf_nonempty(client: TestClient) -> None:
    r = client.get("/invoices/1/pdf")
    assert len(r.content) > 0


def test_invoice_9999_pdf_returns_404(client: TestClient) -> None:
    r = client.get("/invoices/9999/pdf")
    assert r.status_code == 404


def test_invoice_9999_pdf_detail(client: TestClient) -> None:
    r = client.get("/invoices/9999/pdf")
    assert r.json()["detail"] == "Invoice 9999 not found"
