"""
Billing engine — assembles a Bill from stored line items.

No FastAPI / HTTP imports. No SQLAlchemy model imports.
build_bill() accepts an injected Session so it is testable in isolation.
assemble_bill() is pure (no I/O) and is the unit-testable core.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.billing import repository
from app.billing.repository import BillInputs
from app.billing.schemas import Bill, BillLine, PaymentInfo, ServiceGroup, Summary, UsageInfo
from app.core.money import money_sum, quantize


def _customer_segment(customer_type: str | None) -> str:
    return "BUSINESS" if (customer_type or "").upper() == "BUSINESS" else "HOME"


def assemble_bill(inputs: BillInputs) -> Bill:
    """
    Pure function: BillInputs → Bill.

    Implements the formulas from docs/BILLING.md §2:
        charges_total      = sum(non-TAX line amounts)
        taxes_total        = sum(TAX line amounts)
        charges_for_period = charges_total + taxes_total
        payments_received  = sum(payment amounts)
        arrears            = balance_bf − payments_received
        total_payable      = arrears + charges_for_period
    """
    charge_lines = [li for li in inputs.line_items if li.line_type != "TAX"]
    tax_lines_raw = [li for li in inputs.line_items if li.line_type == "TAX"]

    charges_total      = money_sum(li.amount for li in charge_lines)
    taxes_total        = money_sum(li.amount for li in tax_lines_raw)
    charges_for_period = quantize(charges_total + taxes_total)

    payments_received  = money_sum(p.amount for p in inputs.payments)
    arrears            = quantize(inputs.balance_bf - payments_received)
    total_payable      = quantize(arrears + charges_for_period)

    # ── Group charge lines under their sub-account heading ────────────────
    # Preserve the insertion order of service_accounts (matches the bill layout).
    groups: list[ServiceGroup] = []
    for svc in inputs.service_accounts:
        svc_lines = [
            li for li in charge_lines
            if li.service_number == svc.service_number
        ]
        if not svc_lines:
            continue
        groups.append(ServiceGroup(
            service_number=svc.service_number,
            service_type=svc.service_type,
            label=svc.label,
            lines=[
                BillLine(
                    service_number=li.service_number,
                    line_type=li.line_type,
                    description=li.description,
                    period_start=li.period_start,
                    period_end=li.period_end,
                    amount=li.amount,
                )
                for li in svc_lines
            ],
        ))

    # ── Global lines that are not tied to a sub-account (TAX, FEE, …) ─────
    tax_lines = [
        BillLine(
            service_number=None,
            line_type=li.line_type,
            description=li.description,
            period_start=li.period_start,
            period_end=li.period_end,
            amount=li.amount,
        )
        for li in tax_lines_raw
    ]

    # ── Customer address — compact to non-empty lines ─────────────────────
    address_lines = [
        s for s in [
            inputs.address_line1,
            inputs.address_line2,
            " ".join(filter(None, [inputs.city, inputs.postal_code])) or None,
        ]
        if s
    ]

    return Bill(
        account_number=inputs.account_number,
        telephone_number=inputs.telephone_number,
        service_label=inputs.service_label,
        customer_segment=_customer_segment(inputs.customer_type),
        customer_name=inputs.customer_name,
        address_lines=address_lines,
        invoice_number=inputs.invoice_number,
        billing_date=inputs.billing_date,
        period_start=inputs.period_start,
        period_end=inputs.period_end,
        due_date=inputs.due_date,
        groups=groups,
        tax_lines=tax_lines,
        charges_total=charges_total,
        taxes_total=taxes_total,
        summary=Summary(
            balance_bf=inputs.balance_bf,
            payments_received=payments_received,
            arrears=arrears,
            charges_for_period=charges_for_period,
            total_payable=total_payable,
        ),
        payments=[
            PaymentInfo(
                payment_date=p.payment_date,
                method=p.method,
                amount=p.amount,
                reference=p.reference,
            )
            for p in inputs.payments
        ],
        usage_records=[
            UsageInfo(
                event_time=u.event_time,
                service_number=u.service_number,
                service_type=u.service_type,
                description=u.description or "",
                charge=u.charge,
            )
            for u in inputs.usage_records
        ],
    )


def build_bill(
    session: Session,
    account_number: str,
    period_start: date,
    period_end: date,
) -> Bill:
    """Fetch from DB then assemble. Session is provided by the caller."""
    inputs = repository.get_bill_inputs(account_number, period_start, period_end, session)
    return assemble_bill(inputs)
