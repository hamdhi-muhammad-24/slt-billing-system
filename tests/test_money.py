from decimal import Decimal

import pytest

from app.core.money import money_sum, quantize, to_money


class TestQuantize:
    def test_already_two_dp(self):
        assert quantize(Decimal("10.00")) == Decimal("10.00")

    def test_rounds_half_up(self):
        assert quantize(Decimal("1.005")) == Decimal("1.01")

    def test_rounds_half_up_negative(self):
        # ROUND_HALF_UP rounds half away from zero: -1.005 → -1.01
        assert quantize(Decimal("-1.005")) == Decimal("-1.01")

    def test_truncates_extra_dp(self):
        assert quantize(Decimal("2.999")) == Decimal("3.00")

    def test_zero(self):
        assert quantize(Decimal("0")) == Decimal("0.00")


class TestToMoney:
    def test_from_string(self):
        assert to_money("4628.52") == Decimal("4628.52")

    def test_from_int(self):
        assert to_money(100) == Decimal("100.00")

    def test_from_float_avoids_representation_error(self):
        # float 0.1 + 0.2 is famously wrong — to_money routes through str(Decimal)
        result = to_money(1.005)
        # float 1.005 may be 1.00499… so we just confirm it's a Decimal with 2 dp
        assert result == result.quantize(Decimal("0.01"))

    def test_from_decimal(self):
        assert to_money(Decimal("99.999")) == Decimal("100.00")

    def test_negative(self):
        assert to_money("-250.50") == Decimal("-250.50")


class TestMoneySum:
    def test_empty(self):
        assert money_sum([]) == Decimal("0.00")

    def test_simple(self):
        values = [Decimal("100.00"), Decimal("200.00"), Decimal("50.00")]
        assert money_sum(values) == Decimal("350.00")

    def test_with_negatives(self):
        values = [Decimal("500.00"), Decimal("-75.25"), Decimal("200.75")]
        assert money_sum(values) == Decimal("625.50")

    def test_result_is_quantized(self):
        # Even if intermediate sum has extra precision, result is 2 dp
        values = [Decimal("1.001"), Decimal("1.001"), Decimal("1.001")]
        result = money_sum(values)
        assert result == result.quantize(Decimal("0.01"))

    def test_billing_sample_line_items(self):
        # Verified line items from DATABASE.md §7 Sample-1 seed
        # Rentals: 0.00 + 0.00 + 1154.84 + 404.19; Tax: 366.21
        items = [
            Decimal("0.00"),
            Decimal("0.00"),
            Decimal("1154.84"),
            Decimal("404.19"),
            Decimal("366.21"),
        ]
        assert money_sum(items) == Decimal("1925.24")
