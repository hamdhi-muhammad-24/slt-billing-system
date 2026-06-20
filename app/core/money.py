from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable

_TWO_PLACES = Decimal("0.01")


def quantize(value: Decimal) -> Decimal:
    return value.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)


def to_money(value: int | float | str | Decimal) -> Decimal:
    return quantize(Decimal(str(value)))


def money_sum(values: Iterable[Decimal]) -> Decimal:
    return quantize(sum(values, Decimal("0")))
