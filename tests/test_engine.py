"""
Unit tests for the billing engine (assemble_bill).

All tests construct BillInputs directly — no database, no session.
The golden test verifies Sample-1 from docs/DATABASE.md §7.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.billing.engine import assemble_bill
from app.billing.repository import (
    BillInputs,
    LineItemRow,
    PaymentRow,
    ServiceAccountRow,
    UsageRecordRow,
)

# ---------------------------------------------------------------------------
# Sample-1 fixture — exact data from docs/DATABASE.md §7
# ---------------------------------------------------------------------------

_PERIOD_START = date(2024, 1, 24)
_PERIOD_END   = date(2024, 2, 23)


def _sample1() -> BillInputs:
    return BillInputs(
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
            ServiceAccountRow(
                id=1, service_number="0359236535",
                service_type="VOICE", label="SLT Voice Service 4G Net pal",
            ),
            ServiceAccountRow(
                id=2, service_number="940359236535",
                service_type="BROADBAND",
                label="SLT BroadBand Service LTE Web Family Plus",
            ),
        ],
        line_items=[
            LineItemRow(1, "0359236535", "VOICE", "RENTAL",
                        "SLT Voice Service 4G Net pal [Rental]",
                        date(2024, 1, 24), date(2024, 2, 16), Decimal("0.00"), 1),
            LineItemRow(1, "0359236535", "VOICE", "RENTAL",
                        "SLT Voice Service 4G Net pal [Rental]",
                        date(2024, 2, 17), date(2024, 2, 23), Decimal("0.00"), 2),
            LineItemRow(2, "940359236535", "BROADBAND", "RENTAL",
                        "SLT BroadBand Service LTE Web Family Plus [Rental]",
                        date(2024, 1, 24), date(2024, 2, 12), Decimal("1154.84"), 3),
            LineItemRow(2, "940359236535", "BROADBAND", "RENTAL",
                        "SLT BroadBand Service LTE Web Family Plus [Rental]",
                        date(2024, 2, 17), date(2024, 2, 23), Decimal("404.19"), 4),
            LineItemRow(None, None, None, "TAX",
                        "Taxes & Levies", None, None, Decimal("366.21"), 99),
        ],
        payments=[
            PaymentRow(date(2024, 2, 16), "PHYSICAL", Decimal("5000.00"), "Physical payment"),
        ],
    )


# ---------------------------------------------------------------------------
# Helper — build minimal BillInputs with overrides
# ---------------------------------------------------------------------------

def _base(**overrides) -> BillInputs:
    """Minimal all-zero BillInputs; override fields as needed."""
    defaults: dict = dict(
        account_number="TST-001",
        telephone_number=None,
        service_label=None,
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


# ---------------------------------------------------------------------------
# Golden tests (Sample-1) ── the numbers every future change must not break
# ---------------------------------------------------------------------------

class TestSample1Golden:
    def test_total_payable(self):
        bill = assemble_bill(_sample1())
        assert bill.summary.total_payable == Decimal("4628.52")

    def test_charges_total(self):
        bill = assemble_bill(_sample1())
        assert bill.charges_total == Decimal("1559.03")   # 0+0+1154.84+404.19

    def test_taxes_total(self):
        bill = assemble_bill(_sample1())
        assert bill.taxes_total == Decimal("366.21")

    def test_charges_for_period(self):
        bill = assemble_bill(_sample1())
        assert bill.summary.charges_for_period == Decimal("1925.24")  # 1559.03+366.21

    def test_arrears(self):
        bill = assemble_bill(_sample1())
        assert bill.summary.arrears == Decimal("2703.28")  # 7703.28 − 5000

    def test_payments_received(self):
        bill = assemble_bill(_sample1())
        assert bill.summary.payments_received == Decimal("5000.00")

    def test_balance_bf_preserved(self):
        bill = assemble_bill(_sample1())
        assert bill.summary.balance_bf == Decimal("7703.28")

    def test_invoice_number(self):
        bill = assemble_bill(_sample1())
        assert bill.invoice_number == "0038474527-0337"

    def test_customer_name(self):
        bill = assemble_bill(_sample1())
        assert bill.customer_name == "Pavithim Nayapila Senadira"

    def test_address_lines(self):
        bill = assemble_bill(_sample1())
        assert bill.address_lines == ["No 807/102 Welimada Road", "Badulla 90200"]

    def test_two_service_groups(self):
        bill = assemble_bill(_sample1())
        assert len(bill.groups) == 2

    def test_group_order(self):
        bill = assemble_bill(_sample1())
        assert bill.groups[0].service_number == "0359236535"
        assert bill.groups[1].service_number == "940359236535"

    def test_group_service_types(self):
        bill = assemble_bill(_sample1())
        assert bill.groups[0].service_type == "VOICE"
        assert bill.groups[1].service_type == "BROADBAND"

    def test_voice_group_has_two_lines(self):
        bill = assemble_bill(_sample1())
        voice = bill.groups[0]
        assert len(voice.lines) == 2
        assert all(li.amount == Decimal("0.00") for li in voice.lines)

    def test_broadband_group_has_two_lines(self):
        bill = assemble_bill(_sample1())
        bb = bill.groups[1]
        assert len(bb.lines) == 2
        assert bb.lines[0].amount == Decimal("1154.84")
        assert bb.lines[1].amount == Decimal("404.19")

    def test_one_tax_line(self):
        bill = assemble_bill(_sample1())
        assert len(bill.tax_lines) == 1
        assert bill.tax_lines[0].amount == Decimal("366.21")
        assert bill.tax_lines[0].service_number is None

    def test_one_payment(self):
        bill = assemble_bill(_sample1())
        assert len(bill.payments) == 1
        assert bill.payments[0].method == "PHYSICAL"
        assert bill.payments[0].amount == Decimal("5000.00")

    def test_usage_records_preserved(self):
        inputs = _sample1()
        inputs.usage_records = [
            UsageRecordRow(
                service_number="0359236535",
                service_type="PEOTV",
                event_time=datetime(2024, 2, 3, 19, 30),
                description="Additional Channels",
                charge=Decimal("125.00"),
            )
        ]
        bill = assemble_bill(inputs)
        assert len(bill.usage_records) == 1
        assert bill.usage_records[0].description == "Additional Channels"
        assert bill.usage_records[0].charge == Decimal("125.00")

    def test_customer_type_maps_to_home_or_business_segment(self):
        residential = assemble_bill(_sample1())
        assert residential.customer_segment == "HOME"

        business_inputs = _sample1()
        business_inputs.customer_type = "BUSINESS"
        business = assemble_bill(business_inputs)
        assert business.customer_segment == "BUSINESS"


# ---------------------------------------------------------------------------
# Summary invariant — total_payable == arrears + charges_for_period
# ---------------------------------------------------------------------------

class TestSummaryInvariant:
    @pytest.mark.parametrize("balance_bf,paid,charges,taxes,expected_tp", [
        ("7703.28", "5000.00", "1559.03", "366.21", "4628.52"),   # Sample-1
        ("2000.00", "1500.00", "1800.00", "270.00", "2570.00"),   # single BB
        ("3200.00", "0.00",    "1800.00", "270.00", "5270.00"),   # carried arrears
        ("0.00",    "0.00",    "0.00",    "0.00",   "0.00"),      # zero balance
        ("2000.00", "2000.00", "2250.00", "337.50", "2587.50"),   # with discount
        ("500.00",  "500.00",  "350.00",  "52.50",  "402.50"),    # exact payment
    ])
    def test_invariant(self, balance_bf, paid, charges, taxes, expected_tp):
        charges_d = Decimal(charges)
        taxes_d   = Decimal(taxes)
        paid_d    = Decimal(paid)
        line_items = []
        if charges_d != Decimal("0"):
            line_items.append(LineItemRow(
                99, "0990000000", "BROADBAND", "RENTAL", "Rental",
                _PERIOD_START, _PERIOD_END, charges_d, 1,
            ))
        if taxes_d != Decimal("0"):
            line_items.append(LineItemRow(
                None, None, None, "TAX", "Taxes & Levies",
                None, None, taxes_d, 99,
            ))
        pmts = (
            [PaymentRow(date(2024, 2, 10), "PHYSICAL", paid_d, None)]
            if paid_d else []
        )
        inputs = _base(
            balance_bf=Decimal(balance_bf),
            line_items=line_items,
            payments=pmts,
        )
        bill = assemble_bill(inputs)
        assert bill.summary.total_payable == Decimal(expected_tp)
        # Invariant must hold exactly
        assert bill.summary.total_payable == (
            bill.summary.arrears + bill.summary.charges_for_period
        )


# ---------------------------------------------------------------------------
# Edge case: no payments → arrears = balance_bf
# ---------------------------------------------------------------------------

class TestNoPayments:
    def test_arrears_equals_balance_bf(self):
        inputs = _base(
            balance_bf=Decimal("3200.00"),
            payments=[],
            line_items=[
                LineItemRow(99, "0990000000", "BROADBAND", "RENTAL", "Rental",
                            _PERIOD_START, _PERIOD_END, Decimal("1800.00"), 1),
                LineItemRow(None, None, None, "TAX", "Taxes & Levies",
                            None, None, Decimal("270.00"), 99),
            ],
        )
        bill = assemble_bill(inputs)
        assert bill.summary.payments_received == Decimal("0.00")
        assert bill.summary.arrears == Decimal("3200.00")
        assert bill.summary.total_payable == Decimal("5270.00")

    def test_total_payable_equals_balance_plus_charges(self):
        inputs = _base(balance_bf=Decimal("1000.00"), payments=[])
        bill = assemble_bill(inputs)
        assert bill.summary.total_payable == Decimal("1000.00")


# ---------------------------------------------------------------------------
# Edge case: negative DISCOUNT line
# ---------------------------------------------------------------------------

class TestDiscountLine:
    def test_discount_reduces_charges_total(self):
        inputs = _base(
            balance_bf=Decimal("0.00"),
            line_items=[
                LineItemRow(99, "0990000000", "BROADBAND", "RENTAL", "Rental",
                            _PERIOD_START, _PERIOD_END, Decimal("2500.00"), 1),
                LineItemRow(99, "0990000000", "BROADBAND", "DISCOUNT", "Loyalty discount",
                            None, None, Decimal("-250.00"), 2),
                LineItemRow(None, None, None, "TAX", "Taxes & Levies",
                            None, None, Decimal("337.50"), 99),
            ],
        )
        bill = assemble_bill(inputs)
        assert bill.charges_total == Decimal("2250.00")    # 2500 − 250
        assert bill.taxes_total == Decimal("337.50")
        assert bill.summary.total_payable == Decimal("2587.50")

    def test_discount_line_appears_in_its_service_group(self):
        inputs = _base(
            line_items=[
                LineItemRow(99, "0990000000", "BROADBAND", "RENTAL", "Rental",
                            _PERIOD_START, _PERIOD_END, Decimal("2500.00"), 1),
                LineItemRow(99, "0990000000", "BROADBAND", "DISCOUNT", "Loyalty discount",
                            None, None, Decimal("-250.00"), 2),
            ],
        )
        bill = assemble_bill(inputs)
        assert len(bill.groups) == 1
        assert len(bill.groups[0].lines) == 2
        discount = bill.groups[0].lines[1]
        assert discount.line_type == "DISCOUNT"
        assert discount.amount == Decimal("-250.00")


# ---------------------------------------------------------------------------
# Edge case: zero balance (no charges, no payments, no arrears)
# ---------------------------------------------------------------------------

class TestZeroBalance:
    def test_all_totals_zero(self):
        bill = assemble_bill(_base())
        assert bill.charges_total == Decimal("0.00")
        assert bill.taxes_total == Decimal("0.00")
        assert bill.summary.charges_for_period == Decimal("0.00")
        assert bill.summary.arrears == Decimal("0.00")
        assert bill.summary.total_payable == Decimal("0.00")

    def test_no_groups_when_no_lines(self):
        bill = assemble_bill(_base())
        assert bill.groups == []
        assert bill.tax_lines == []


# ---------------------------------------------------------------------------
# Edge case: single vs multiple sub-accounts (grouping logic)
# ---------------------------------------------------------------------------

class TestGrouping:
    def test_single_sub_account_produces_one_group(self):
        inputs = _base(
            line_items=[
                LineItemRow(99, "0990000000", "BROADBAND", "RENTAL", "Rental",
                            _PERIOD_START, _PERIOD_END, Decimal("1500.00"), 1),
            ],
        )
        bill = assemble_bill(inputs)
        assert len(bill.groups) == 1
        assert bill.groups[0].service_number == "0990000000"

    def test_three_sub_accounts_three_groups(self):
        inputs = _base(
            service_accounts=[
                ServiceAccountRow(1, "V001", "VOICE",     "Voice"),
                ServiceAccountRow(2, "B001", "BROADBAND", "Broadband"),
                ServiceAccountRow(3, "T001", "PEOTV",     "PeoTV"),
            ],
            line_items=[
                LineItemRow(1, "V001", "VOICE",     "RENTAL", "Voice rental",
                            _PERIOD_START, _PERIOD_END, Decimal("250.00"), 1),
                LineItemRow(2, "B001", "BROADBAND", "RENTAL", "BB rental",
                            _PERIOD_START, _PERIOD_END, Decimal("1500.00"), 2),
                LineItemRow(3, "T001", "PEOTV",     "RENTAL", "TV rental",
                            _PERIOD_START, _PERIOD_END, Decimal("450.00"), 3),
                LineItemRow(None, None, None, "TAX", "Taxes & Levies",
                            None, None, Decimal("330.00"), 99),
            ],
            balance_bf=Decimal("3500.00"),
            payments=[PaymentRow(date(2024, 2, 12), "PHYSICAL", Decimal("3000.00"), None)],
        )
        bill = assemble_bill(inputs)
        assert len(bill.groups) == 3
        assert [g.service_type for g in bill.groups] == ["VOICE", "BROADBAND", "PEOTV"]
        assert bill.charges_total == Decimal("2200.00")
        assert bill.taxes_total == Decimal("330.00")
        assert bill.summary.total_payable == Decimal("3030.00")

    def test_service_account_with_no_lines_omitted_from_groups(self):
        inputs = _base(
            service_accounts=[
                ServiceAccountRow(1, "V001", "VOICE",     "Voice"),
                ServiceAccountRow(2, "B001", "BROADBAND", "Broadband"),
            ],
            line_items=[
                # Only BROADBAND has a charge line; VOICE has zero-amount lines omitted here.
                LineItemRow(2, "B001", "BROADBAND", "RENTAL", "BB rental",
                            _PERIOD_START, _PERIOD_END, Decimal("1500.00"), 1),
            ],
        )
        bill = assemble_bill(inputs)
        assert len(bill.groups) == 1
        assert bill.groups[0].service_type == "BROADBAND"

    def test_lines_stay_in_their_group(self):
        inputs = _base(
            service_accounts=[
                ServiceAccountRow(1, "V001", "VOICE",     "Voice"),
                ServiceAccountRow(2, "B001", "BROADBAND", "Broadband"),
            ],
            line_items=[
                LineItemRow(1, "V001", "VOICE",     "RENTAL", "Voice",
                            _PERIOD_START, _PERIOD_END, Decimal("300.00"), 1),
                LineItemRow(2, "B001", "BROADBAND", "RENTAL", "BB",
                            _PERIOD_START, _PERIOD_END, Decimal("1500.00"), 2),
            ],
        )
        bill = assemble_bill(inputs)
        voice = next(g for g in bill.groups if g.service_type == "VOICE")
        bb    = next(g for g in bill.groups if g.service_type == "BROADBAND")
        assert voice.lines[0].amount == Decimal("300.00")
        assert bb.lines[0].amount    == Decimal("1500.00")


# ---------------------------------------------------------------------------
# Edge case: exact payment (arrears = 0)
# ---------------------------------------------------------------------------

class TestExactPayment:
    def test_zero_arrears(self):
        inputs = _base(
            balance_bf=Decimal("500.00"),
            payments=[PaymentRow(date(2024, 2, 11), "PHYSICAL", Decimal("500.00"), None)],
            line_items=[
                LineItemRow(99, "0990000000", "BROADBAND", "RENTAL", "Rental",
                            _PERIOD_START, _PERIOD_END, Decimal("350.00"), 1),
                LineItemRow(None, None, None, "TAX", "Taxes & Levies",
                            None, None, Decimal("52.50"), 99),
            ],
        )
        bill = assemble_bill(inputs)
        assert bill.summary.arrears == Decimal("0.00")
        assert bill.summary.total_payable == Decimal("402.50")


# ---------------------------------------------------------------------------
# Schema validator fires on bad Summary
# ---------------------------------------------------------------------------

class TestSchemaValidation:
    def test_summary_validator_catches_wrong_total(self):
        from app.billing.schemas import Summary
        with pytest.raises(ValidationError) as exc_info:
            Summary(
                balance_bf=Decimal("1000.00"),
                payments_received=Decimal("500.00"),
                arrears=Decimal("500.00"),
                charges_for_period=Decimal("100.00"),
                total_payable=Decimal("999.99"),   # wrong — should be 600.00
            )
        assert "≠" in str(exc_info.value)

    def test_summary_validator_passes_correct_total(self):
        from app.billing.schemas import Summary
        s = Summary(
            balance_bf=Decimal("1000.00"),
            payments_received=Decimal("500.00"),
            arrears=Decimal("500.00"),
            charges_for_period=Decimal("100.00"),
            total_payable=Decimal("600.00"),
        )
        assert s.total_payable == Decimal("600.00")


# ---------------------------------------------------------------------------
# Edge case: discount-ONLY period (no rental line at all)
# ---------------------------------------------------------------------------

class TestDiscountOnly:
    """A billing period where the sole non-TAX entry is a negative DISCOUNT."""

    def _inputs(self) -> BillInputs:
        return _base(
            balance_bf=Decimal("500.00"),
            payments=[],
            service_accounts=[
                ServiceAccountRow(99, "0990000000", "BROADBAND", "Test Broadband"),
            ],
            line_items=[
                LineItemRow(
                    99, "0990000000", "BROADBAND", "DISCOUNT",
                    "Service credit",
                    None, None, Decimal("-250.00"), 1,
                ),
            ],
        )

    def test_charges_total_is_negative(self):
        bill = assemble_bill(self._inputs())
        assert bill.charges_total == Decimal("-250.00")

    def test_taxes_total_is_zero(self):
        bill = assemble_bill(self._inputs())
        assert bill.taxes_total == Decimal("0.00")

    def test_charges_for_period_is_negative(self):
        bill = assemble_bill(self._inputs())
        assert bill.summary.charges_for_period == Decimal("-250.00")

    def test_total_payable_correct(self):
        # arrears = 500 - 0 = 500; total = 500 + (-250) = 250
        bill = assemble_bill(self._inputs())
        assert bill.summary.arrears == Decimal("500.00")
        assert bill.summary.total_payable == Decimal("250.00")

    def test_discount_line_appears_in_group(self):
        bill = assemble_bill(self._inputs())
        assert len(bill.groups) == 1
        assert len(bill.groups[0].lines) == 1
        assert bill.groups[0].lines[0].line_type == "DISCOUNT"
        assert bill.groups[0].lines[0].amount == Decimal("-250.00")

    def test_summary_invariant_holds(self):
        bill = assemble_bill(self._inputs())
        assert bill.summary.total_payable == (
            bill.summary.arrears + bill.summary.charges_for_period
        )

    def test_net_credit_when_balance_zero(self):
        """Discount alone with zero balance_bf produces a negative total_payable (credit)."""
        inputs = _base(
            balance_bf=Decimal("0.00"),
            payments=[],
            line_items=[
                LineItemRow(
                    99, "0990000000", "BROADBAND", "DISCOUNT",
                    "Full service credit",
                    None, None, Decimal("-300.00"), 1,
                ),
            ],
        )
        bill = assemble_bill(inputs)
        assert bill.summary.total_payable == Decimal("-300.00")
        assert bill.summary.total_payable == (
            bill.summary.arrears + bill.summary.charges_for_period
        )


# ---------------------------------------------------------------------------
# Edge case: multiple payments in the same period
# ---------------------------------------------------------------------------

class TestMultiplePayments:
    def test_two_payments_are_summed(self):
        inputs = _base(
            balance_bf=Decimal("1000.00"),
            payments=[
                PaymentRow(date(2024, 2, 5),  "PHYSICAL", Decimal("400.00"), "Receipt 1"),
                PaymentRow(date(2024, 2, 18), "ONLINE",   Decimal("600.00"), "Receipt 2"),
            ],
            line_items=[
                LineItemRow(99, "0990000000", "BROADBAND", "RENTAL", "Rental",
                            _PERIOD_START, _PERIOD_END, Decimal("1800.00"), 1),
            ],
        )
        bill = assemble_bill(inputs)
        assert bill.summary.payments_received == Decimal("1000.00")
        assert bill.summary.arrears == Decimal("0.00")
        assert len(bill.payments) == 2

    def test_three_payments_all_counted(self):
        inputs = _base(
            balance_bf=Decimal("0.00"),
            payments=[
                PaymentRow(date(2024, 2, 1), "PHYSICAL", Decimal("100.00"), None),
                PaymentRow(date(2024, 2, 8), "CARD",     Decimal("200.00"), None),
                PaymentRow(date(2024, 2, 15), "ONLINE",  Decimal("300.00"), None),
            ],
        )
        bill = assemble_bill(inputs)
        assert bill.summary.payments_received == Decimal("600.00")
        assert len(bill.payments) == 3

    def test_payment_rounding_does_not_accumulate(self):
        """Summing many small Decimal payments must not drift from the exact total."""
        inputs = _base(
            balance_bf=Decimal("0.00"),
            payments=[
                PaymentRow(date(2024, 2, i + 1), "PHYSICAL", Decimal("0.01"), None)
                for i in range(10)
            ],
        )
        bill = assemble_bill(inputs)
        assert bill.summary.payments_received == Decimal("0.10")


# ---------------------------------------------------------------------------
# Edge case: overpayment (payment exceeds balance_bf → negative arrears)
# ---------------------------------------------------------------------------

class TestOverpayment:
    def test_negative_arrears(self):
        inputs = _base(
            balance_bf=Decimal("300.00"),
            payments=[PaymentRow(date(2024, 2, 10), "ONLINE", Decimal("500.00"), None)],
            line_items=[
                LineItemRow(99, "0990000000", "BROADBAND", "RENTAL", "Rental",
                            _PERIOD_START, _PERIOD_END, Decimal("1200.00"), 1),
            ],
        )
        bill = assemble_bill(inputs)
        assert bill.summary.payments_received == Decimal("500.00")
        assert bill.summary.arrears == Decimal("-200.00")
        assert bill.summary.total_payable == Decimal("1000.00")  # -200 + 1200
        assert bill.summary.total_payable == (
            bill.summary.arrears + bill.summary.charges_for_period
        )

    def test_full_overpayment_gives_credit(self):
        """If payment covers balance AND period charges the bill shows a credit."""
        inputs = _base(
            balance_bf=Decimal("500.00"),
            payments=[PaymentRow(date(2024, 2, 10), "ONLINE", Decimal("1500.00"), None)],
            line_items=[
                LineItemRow(99, "0990000000", "BROADBAND", "RENTAL", "Rental",
                            _PERIOD_START, _PERIOD_END, Decimal("800.00"), 1),
            ],
        )
        bill = assemble_bill(inputs)
        assert bill.summary.arrears == Decimal("-1000.00")
        assert bill.summary.total_payable == Decimal("-200.00")   # credit
        assert bill.summary.total_payable == (
            bill.summary.arrears + bill.summary.charges_for_period
        )


# ---------------------------------------------------------------------------
# Address formatting
# ---------------------------------------------------------------------------

class TestAddressFormatting:
    def test_none_address2_is_omitted(self):
        inputs = _base(address_line1="10 Main St", address_line2=None,
                       city="Galle", postal_code="80000")
        bill = assemble_bill(inputs)
        assert bill.address_lines == ["10 Main St", "Galle 80000"]

    def test_address2_included_when_present(self):
        inputs = _base(address_line1="12 Galle Rd", address_line2="Polhena",
                       city="Matara", postal_code="81000")
        bill = assemble_bill(inputs)
        assert bill.address_lines == ["12 Galle Rd", "Polhena", "Matara 81000"]
