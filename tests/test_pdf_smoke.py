"""
PDF smoke tests — confirm render_bill produces a valid, non-empty PDF for
representative bill shapes without needing a database connection.

All fixtures use assemble_bill() directly with in-memory BillInputs.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from app.billing.engine import assemble_bill
from app.billing.repository import (
    BillInputs,
    LineItemRow,
    PaymentRow,
    ServiceAccountRow,
    UsageRecordRow,
)
from app.billing.schemas import Bill
from app.pdf.renderer import render_bill

_PERIOD_START = date(2024, 1, 24)
_PERIOD_END   = date(2024, 2, 23)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _base(**overrides) -> BillInputs:
    defaults: dict = dict(
        account_number="TST-001",
        telephone_number="0112345678",
        service_label="Test service",
        customer_name="Test Customer",
        address_line1="1 Test Street",
        address_line2=None,
        city="Colombo",
        postal_code="10000",
        invoice_number="TST-INV-0001",
        billing_date=date(2024, 2, 25),
        period_start=_PERIOD_START,
        period_end=_PERIOD_END,
        due_date=date(2024, 3, 17),
        balance_bf=Decimal("0.00"),
        service_accounts=[
            ServiceAccountRow(99, "0990000000", "BROADBAND", "Test Broadband"),
        ],
        line_items=[],
        payments=[],
    )
    defaults.update(overrides)
    return BillInputs(**defaults)


def _sample1_bill() -> Bill:
    """Exact Sample-1 from docs/DATABASE.md §7 — total_payable must be 4628.52."""
    inputs = BillInputs(
        account_number="004 152 4075",
        telephone_number="0359236535",
        service_label="LTE service",
        customer_name="Pavithim Nayapila Senadira",
        address_line1="No 807/102 Welimada Road",
        address_line2=None,
        city="Badulla",
        postal_code="90200",
        invoice_number="0038474527-0337",
        billing_date=date(2024, 2, 25),
        period_start=_PERIOD_START,
        period_end=_PERIOD_END,
        due_date=date(2024, 3, 17),
        balance_bf=Decimal("7703.28"),
        service_accounts=[
            ServiceAccountRow(1, "0359236535",   "VOICE",     "SLT Voice Service 4G Net pal"),
            ServiceAccountRow(2, "940359236535", "BROADBAND", "SLT BroadBand Service LTE Web Family Plus"),
        ],
        line_items=[
            LineItemRow(1, "0359236535",   "VOICE",     "RENTAL",
                        "SLT Voice Service 4G Net pal [Rental]",
                        date(2024, 1, 24), date(2024, 2, 16), Decimal("0.00"), 1),
            LineItemRow(1, "0359236535",   "VOICE",     "RENTAL",
                        "SLT Voice Service 4G Net pal [Rental]",
                        date(2024, 2, 17), date(2024, 2, 23), Decimal("0.00"), 2),
            LineItemRow(2, "940359236535", "BROADBAND", "RENTAL",
                        "SLT BroadBand Service LTE Web Family Plus [Rental]",
                        date(2024, 1, 24), date(2024, 2, 12), Decimal("1154.84"), 3),
            LineItemRow(2, "940359236535", "BROADBAND", "RENTAL",
                        "SLT BroadBand Service LTE Web Family Plus [Rental]",
                        date(2024, 2, 17), date(2024, 2, 23), Decimal("404.19"), 4),
            LineItemRow(None, None, None, "TAX", "Taxes & Levies",
                        None, None, Decimal("366.21"), 99),
        ],
        payments=[
            PaymentRow(date(2024, 2, 16), "PHYSICAL", Decimal("5000.00"), "Physical payment"),
        ],
    )
    return assemble_bill(inputs)


def _assert_valid_pdf(path: str) -> None:
    """Assert the file exists, is non-empty, and starts with the PDF magic bytes."""
    p = Path(path)
    assert p.exists(), f"PDF not found: {path}"
    size = p.stat().st_size
    assert size > 0, "PDF is empty"
    header = p.read_bytes()[:4]
    assert header == b"%PDF", f"File does not start with %PDF — got {header!r}"


def _page_count(path: str) -> int:
    """Count /Type /Page objects in the raw PDF bytes (heuristic, good enough for smoke)."""
    import re
    data = Path(path).read_bytes()
    return len(re.findall(rb"/Type\s*/Page\b", data))


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------

class TestPdfSmoke:
    def test_sample1_produces_file(self, tmp_path):
        out = str(tmp_path / "sample1.pdf")
        render_bill(_sample1_bill(), out)
        _assert_valid_pdf(out)

    def test_sample1_is_single_page(self, tmp_path):
        out = str(tmp_path / "sample1.pdf")
        render_bill(_sample1_bill(), out)
        assert _page_count(out) == 1

    def test_sample1_total_payable_unchanged(self, tmp_path):
        """Rendering must not mutate the Bill's computed totals."""
        bill = _sample1_bill()
        out  = str(tmp_path / "sample1.pdf")
        render_bill(bill, out)
        assert bill.summary.total_payable == Decimal("4628.52")

    def test_zero_charges_produces_file(self, tmp_path):
        """An account with no line items (no charges, no payments) renders without error."""
        out = str(tmp_path / "zero.pdf")
        render_bill(assemble_bill(_base()), out)
        _assert_valid_pdf(out)

    def test_no_payments_produces_file(self, tmp_path):
        """Account with arrears but no payment this period (OVERDUE-style) renders OK."""
        inputs = _base(
            account_number="007 448 0912",
            balance_bf=Decimal("3200.00"),
            payments=[],
            line_items=[
                LineItemRow(99, "0990000000", "BROADBAND", "RENTAL",
                            "SLT ADSL Unlimited Plus [Rental]",
                            _PERIOD_START, _PERIOD_END, Decimal("1800.00"), 1),
                LineItemRow(None, None, None, "TAX", "Taxes & Levies",
                            None, None, Decimal("270.00"), 99),
            ],
        )
        out = str(tmp_path / "no_payments.pdf")
        render_bill(assemble_bill(inputs), out)
        _assert_valid_pdf(out)

    def test_discount_only_produces_file(self, tmp_path):
        """A period with only a DISCOUNT line (negative charges) renders without error."""
        inputs = _base(
            balance_bf=Decimal("500.00"),
            line_items=[
                LineItemRow(99, "0990000000", "BROADBAND", "DISCOUNT",
                            "Service credit", None, None, Decimal("-250.00"), 1),
            ],
        )
        out = str(tmp_path / "discount_only.pdf")
        render_bill(assemble_bill(inputs), out)
        _assert_valid_pdf(out)

    def test_three_sub_accounts_produces_file(self, tmp_path):
        """Voice + Broadband + PeoTV all render as separate groups."""
        inputs = _base(
            account_number="003 517 2243",
            balance_bf=Decimal("3500.00"),
            service_accounts=[
                ServiceAccountRow(1, "0412230011",   "VOICE",     "SLT Voice Service"),
                ServiceAccountRow(2, "940412230011", "BROADBAND", "SLT Fiber Broadband 100 Mbps"),
                ServiceAccountRow(3, "AD1293847",    "PEOTV",     "PeoTV Package"),
            ],
            payments=[
                PaymentRow(date(2024, 2, 12), "PHYSICAL", Decimal("3000.00"), "Physical payment"),
            ],
            line_items=[
                LineItemRow(1, "0412230011",   "VOICE",     "RENTAL",
                            "SLT Voice Service [Rental]",
                            _PERIOD_START, _PERIOD_END, Decimal("250.00"), 1),
                LineItemRow(2, "940412230011", "BROADBAND", "RENTAL",
                            "SLT Fiber Broadband 100 Mbps [Rental]",
                            _PERIOD_START, _PERIOD_END, Decimal("1500.00"), 2),
                LineItemRow(3, "AD1293847",    "PEOTV",     "RENTAL",
                            "PeoTV Package [Rental]",
                            _PERIOD_START, _PERIOD_END, Decimal("450.00"), 3),
                LineItemRow(None, None, None, "TAX", "Taxes & Levies",
                            None, None, Decimal("330.00"), 99),
            ],
        )
        out = str(tmp_path / "three_svcs.pdf")
        render_bill(assemble_bill(inputs), out)
        _assert_valid_pdf(out)

    def test_none_telephone_number_produces_file(self, tmp_path):
        """telephone_number=None is valid; the slip field must render an empty string."""
        inputs = _base(telephone_number=None)
        out = str(tmp_path / "no_tel.pdf")
        render_bill(assemble_bill(inputs), out)
        _assert_valid_pdf(out)

    def test_long_address_produces_file(self, tmp_path):
        """Three-line address (line1 + line2 + city+postal) must not overflow."""
        inputs = _base(
            address_line1="No 807/102 Very Long Address Name Road",
            address_line2="Welimada Village, Sub-district",
            city="Badulla",
            postal_code="90200",
        )
        out = str(tmp_path / "long_addr.pdf")
        render_bill(assemble_bill(inputs), out)
        _assert_valid_pdf(out)

    def test_usage_records_render_usage_table(self, tmp_path):
        """Optional usage rows render in the lower-right usage detail table."""
        inputs = _base(
            usage_records=[
                UsageRecordRow(
                    service_number="0990000000",
                    service_type="PEOTV",
                    event_time=datetime(2024, 2, 3, 19, 30),
                    description="Additional Channels",
                    charge=Decimal("125.00"),
                )
            ],
        )
        bill = assemble_bill(inputs)
        assert len(bill.usage_records) == 1
        out = str(tmp_path / "usage.pdf")
        render_bill(bill, out)
        _assert_valid_pdf(out)
