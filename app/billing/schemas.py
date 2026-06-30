"""
Pydantic v2 bill schemas — the only objects the PDF renderer ever touches.
No SQLAlchemy, no FastAPI, no HTTP imports.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


class PaymentInfo(BaseModel):
    payment_date: date
    method: str
    amount: Decimal
    reference: str | None = None


class UsageInfo(BaseModel):
    event_time: datetime | None = None
    service_number: str
    service_type: str
    description: str
    charge: Decimal


class BillLine(BaseModel):
    service_number: str | None = None
    line_type: str
    description: str
    period_start: date | None = None
    period_end: date | None = None
    amount: Decimal


class ServiceGroup(BaseModel):
    service_number: str
    service_type: str
    label: str | None = None
    lines: list[BillLine]


class Summary(BaseModel):
    balance_bf: Decimal
    payments_received: Decimal
    arrears: Decimal
    charges_for_period: Decimal
    total_payable: Decimal

    @model_validator(mode="after")
    def _totals_consistent(self) -> "Summary":
        expected = self.arrears + self.charges_for_period
        if self.total_payable != expected:
            raise ValueError(
                f"total_payable {self.total_payable} ≠ "
                f"arrears {self.arrears} + charges_for_period "
                f"{self.charges_for_period} (= {expected})"
            )
        return self


class Bill(BaseModel):
    # ── header ────────────────────────────────────────────────────────────
    account_number:   str
    telephone_number: str | None = None
    service_label:    str | None = None
    customer_segment: str = "HOME"
    customer_name:    str
    address_lines:    list[str]
    invoice_number:   str
    billing_date:     date
    period_start:     date
    period_end:       date
    due_date:         date
    # ── body ──────────────────────────────────────────────────────────────
    groups:           list[ServiceGroup]   # charge lines grouped by sub-account
    tax_lines:        list[BillLine]       # Taxes & Levies (global lines)
    charges_total:    Decimal
    taxes_total:      Decimal
    summary:          Summary
    payments:         list[PaymentInfo]
    usage_records:    list[UsageInfo] = Field(default_factory=list)
