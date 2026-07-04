from fastapi.testclient import TestClient
from datetime import date
from pathlib import Path

from sqlalchemy import delete, select

from app.db.base import SessionLocal
from app.db.models import Account, BillingRun, BillingRunApproval, BillingSchedule, Invoice, InvoiceTemplate
from app.db.seed import _seed_invoice_templates


def _ensure_templates_seeded() -> None:
    with SessionLocal() as db:
        _seed_invoice_templates(db)
        db.commit()


def test_invoice_templates_list_returns_seeded_templates(client: TestClient) -> None:
    _ensure_templates_seeded()
    response = client.get("/invoice-templates")
    assert response.status_code == 200
    body = response.json()
    system_templates = [template for template in body if template["is_system_template"]]
    assert len(system_templates) >= 18
    assert any(template["template_code"] == "SLT_TEMPLATE_01" for template in system_templates)
    assert sum(1 for template in body if template["is_active"]) == 1


def test_invoice_template_activate_sets_one_active_template(client: TestClient) -> None:
    _ensure_templates_seeded()
    templates = client.get("/invoice-templates").json()
    original_active = next(template for template in templates if template["is_active"])
    target = next(template for template in templates if template["template_code"] == "SLT_TEMPLATE_02")

    response = client.post(f"/invoice-templates/{target['id']}/activate")
    assert response.status_code == 200
    assert response.json()["is_active"] is True

    refreshed = client.get("/invoice-templates").json()
    active_templates = [template for template in refreshed if template["is_active"]]
    assert len(active_templates) == 1
    assert active_templates[0]["id"] == target["id"]

    client.post(f"/invoice-templates/{original_active['id']}/activate")


def test_invoice_template_save_copy_preserves_original(client: TestClient) -> None:
    _ensure_templates_seeded()
    original = next(
        template for template in client.get("/invoice-templates").json()
        if template["template_code"] == "SLT_TEMPLATE_03"
    )

    response = client.post(
        f"/invoice-templates/{original['id']}/save-copy",
        json={
            "name": "Custom test template",
            "header_message": "Custom header",
            "footer_message": "Custom footer",
            "promotion_message": "Custom promotion",
        },
    )
    assert response.status_code == 201
    copy = response.json()
    assert copy["is_system_template"] is False
    assert copy["base_template_id"] == original["id"]
    assert copy["header_message"] == "Custom header"

    refreshed_original = client.get(f"/invoice-templates/{original['id']}").json()
    assert refreshed_original["is_system_template"] is True
    assert refreshed_original["header_message"] == original["header_message"]

    with SessionLocal() as db:
        db.execute(delete(InvoiceTemplate).where(InvoiceTemplate.id == copy["id"]))
        db.commit()


def test_generate_batch_creates_run_items_with_delivery_disabled(client: TestClient) -> None:
    _ensure_templates_seeded()
    with SessionLocal() as db:
        invoice = db.scalar(
            select(Invoice)
            .join(Account, Invoice.account_id == Account.id)
            .where(
                Account.id == 1,
                Invoice.billing_date >= date(2026, 6, 1),
                Invoice.billing_date <= date(2026, 6, 30),
            )
        )
        assert invoice is not None
        previous_pdf_path = invoice.pdf_path
        previous_template_id = invoice.template_id
        previous_status = invoice.status

    response = client.post(
        "/billing/generate-batch",
        json={"period": "2026-06", "account_ids": [1]},
    )
    assert response.status_code == 202
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["account_id"] == 1
    assert item["pdf_status"] == "SUCCESS"
    assert item["email_status"] == "NOT_ENABLED"
    assert item["sms_status"] == "NOT_ENABLED"
    assert item["overall_status"] == "GENERATED"
    assert item["template_id"] == body["template_id"]

    generated_pdf_path = None
    with SessionLocal() as db:
        invoice = db.get(Invoice, item["invoice_id"])
        if invoice is not None:
            generated_pdf_path = invoice.pdf_path
            invoice.pdf_path = previous_pdf_path
            invoice.template_id = previous_template_id
            invoice.status = previous_status
        db.execute(delete(BillingRun).where(BillingRun.id == body["id"]))
        db.commit()

    if generated_pdf_path and generated_pdf_path != previous_pdf_path:
        Path(generated_pdf_path).unlink(missing_ok=True)


def test_billing_schedule_get_and_update(client: TestClient) -> None:
    original = client.get("/billing/schedule").json()
    payload = {
        "name": "Monthly SLT billing",
        "day_of_month": 5,
        "run_time": "03:15",
        "timezone": "Asia/Colombo",
        "schedule_mode": "APPROVAL_REQUIRED",
        "is_active": True,
        "send_email": False,
        "send_sms": True,
        "approval_lead_days": 2,
        "approval_email": "approval@slt.local",
    }
    try:
        response = client.put("/billing/schedule", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["day_of_month"] == 5
        assert body["run_time"] == "03:15"
        assert body["schedule_mode"] == "APPROVAL_REQUIRED"
        assert body["send_email"] is False
        assert body["send_sms"] is True
    finally:
        client.put("/billing/schedule", json={
            "name": original["name"],
            "day_of_month": original["day_of_month"],
            "run_time": original["run_time"],
            "timezone": original["timezone"],
            "schedule_mode": original["schedule_mode"],
            "is_active": original["is_active"],
            "send_email": original["send_email"],
            "send_sms": original["send_sms"],
            "approval_lead_days": original["approval_lead_days"],
            "approval_email": original["approval_email"],
        })


def test_approval_mode_creates_and_approves_request(client: TestClient) -> None:
    original = client.get("/billing/schedule").json()
    period = "2026-06"
    with SessionLocal() as db:
        db.execute(delete(BillingRunApproval).where(BillingRunApproval.period == period))
        schedule = db.scalar(select(BillingSchedule).order_by(BillingSchedule.id).limit(1))
        original_last_triggered_period = schedule.last_triggered_period if schedule else None
        if schedule is not None:
            schedule.last_triggered_period = None
        db.commit()

    try:
        response = client.put("/billing/schedule", json={
            "name": "Monthly SLT billing",
            "day_of_month": 15,
            "run_time": "02:00",
            "timezone": "Asia/Colombo",
            "schedule_mode": "APPROVAL_REQUIRED",
            "is_active": True,
            "send_email": False,
            "send_sms": False,
            "approval_lead_days": 1,
            "approval_email": "approval@slt.local",
        })
        assert response.status_code == 200

        evaluated = client.post(
            "/billing/schedule/evaluate",
            json={"now": "2026-07-14T03:00:00+05:30"},
        )
        assert evaluated.status_code == 200
        result = evaluated.json()
        assert result["action"] == "awaiting_approval"
        assert result["approval_id"] is not None

        approval_id = result["approval_id"]
        approved = client.post(
            f"/billing/schedule/approvals/{approval_id}/approve",
            json={"notes": "approved by test"},
        )
        assert approved.status_code == 200
        body = approved.json()
        assert body["status"] == "APPROVED"
        assert body["period"] == period
    finally:
        client.put("/billing/schedule", json={
            "name": original["name"],
            "day_of_month": original["day_of_month"],
            "run_time": original["run_time"],
            "timezone": original["timezone"],
            "schedule_mode": original["schedule_mode"],
            "is_active": original["is_active"],
            "send_email": original["send_email"],
            "send_sms": original["send_sms"],
            "approval_lead_days": original["approval_lead_days"],
            "approval_email": original["approval_email"],
        })
        with SessionLocal() as db:
            db.execute(delete(BillingRunApproval).where(BillingRunApproval.period == period))
            schedule = db.scalar(select(BillingSchedule).order_by(BillingSchedule.id).limit(1))
            if schedule is not None:
                schedule.last_triggered_period = original_last_triggered_period
            db.commit()


def test_send_billing_run_updates_sms_status_without_email(client: TestClient) -> None:
    _ensure_templates_seeded()
    with SessionLocal() as db:
        invoice = db.scalar(
            select(Invoice)
            .join(Account, Invoice.account_id == Account.id)
            .where(
                Account.id == 1,
                Invoice.billing_date >= date(2026, 6, 1),
                Invoice.billing_date <= date(2026, 6, 30),
            )
        )
        assert invoice is not None
        previous_pdf_path = invoice.pdf_path
        previous_template_id = invoice.template_id
        previous_status = invoice.status

    generated_pdf_path = None
    response = client.post(
        "/billing/generate-batch",
        json={"period": "2026-06", "account_ids": [1]},
    )
    assert response.status_code == 202
    run = response.json()

    sent = client.post(
        f"/billing/runs/{run['id']}/send",
        json={"send_email": False, "send_sms": True},
    )
    assert sent.status_code == 200
    body = sent.json()
    assert body["email_status_summary"]["NOT_ENABLED"] == 1
    assert body["sms_status_summary"]["SUCCESS"] == 1
    assert body["items"][0]["email_status"] == "NOT_ENABLED"
    assert body["items"][0]["sms_status"] == "SUCCESS"
    assert body["items"][0]["overall_status"] == "COMPLETED"

    with SessionLocal() as db:
        invoice = db.get(Invoice, body["items"][0]["invoice_id"])
        if invoice is not None:
            generated_pdf_path = invoice.pdf_path
            invoice.pdf_path = previous_pdf_path
            invoice.template_id = previous_template_id
            invoice.status = previous_status
        db.execute(delete(BillingRun).where(BillingRun.id == run["id"]))
        db.commit()

    if generated_pdf_path and generated_pdf_path != previous_pdf_path:
        Path(generated_pdf_path).unlink(missing_ok=True)
