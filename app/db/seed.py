"""
Synthetic seed data for the SLT e-bill system.

Usage:  python -m app.db.seed
Idempotent — accounts already present (matched by account_number) are skipped.
All monetary values are Decimal; no float arithmetic anywhere.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import configure_logging, get_logger
from app.db.base import SessionLocal
from app.db.models import (
    Account,
    AccountStatus,
    Customer,
    Invoice,
    InvoiceLineItem,
    InvoiceStatus,
    LineType,
    Payment,
    PaymentMethod,
    ServiceAccount,
    ServiceType,
)

log = get_logger(__name__)

# All seed invoices share the same billing window as the real Sample-1.
_BILLING_DATE = date(2024, 2, 25)
_PERIOD_START = date(2024, 1, 24)
_PERIOD_END   = date(2024, 2, 23)
_DUE_DATE     = date(2024, 3, 17)


def _d(s: str) -> Decimal:
    """Construct an exact Decimal from a string literal — never from a float."""
    return Decimal(s)


# ---------------------------------------------------------------------------
# Lightweight spec containers (plain data, no DB session needed)
# ---------------------------------------------------------------------------

@dataclass
class _SvcSpec:
    number: str
    stype:  ServiceType
    label:  str


@dataclass
class _PmtSpec:
    payment_date: date
    method:       PaymentMethod
    amount:       Decimal
    reference:    str | None = None


@dataclass
class _LineSpec:
    svc_number:   str | None   # None → TAX/global line, service_account_id = NULL
    ltype:        LineType
    description:  str
    period_start: date | None
    period_end:   date | None
    amount:       Decimal
    sort_order:   int = 0


@dataclass
class _InvSpec:
    number:             str
    balance_bf:         Decimal
    payments_received:  Decimal
    charges_total:      Decimal
    taxes_total:        Decimal
    charges_for_period: Decimal
    total_payable:      Decimal
    status:             InvoiceStatus  = InvoiceStatus.GENERATED
    lines:              list[_LineSpec] = field(default_factory=list)


@dataclass
class _AcctSpec:
    # Customer
    full_name:     str
    address_line1: str
    address_line2: str | None
    city:          str
    postal_code:   str
    # Account
    account_number:   str
    telephone_number: str | None
    service_label:    str | None
    # Nested
    service_accounts: list[_SvcSpec] = field(default_factory=list)
    payments:         list[_PmtSpec] = field(default_factory=list)
    invoice:          _InvSpec | None = None


# ---------------------------------------------------------------------------
# Seed dataset
# ---------------------------------------------------------------------------

_ACCOUNTS: list[_AcctSpec] = [

    # ── 1. Sample-1 — exact replica of docs/DATABASE.md §7 ─────────────────
    # Voice + Broadband, split-period rentals.
    # Check: 7703.28 − 5000.00 + 1925.24 = 4628.52 ✓
    _AcctSpec(
        full_name="Pavithim Nayapila Senadira",
        address_line1="No 807/102 Welimada Road",
        address_line2=None,
        city="Badulla",
        postal_code="90200",
        account_number="004 152 4075",
        telephone_number="0359236535",
        service_label="LTE service",
        service_accounts=[
            _SvcSpec("0359236535",   ServiceType.VOICE,     "SLT Voice Service 4G Net pal"),
            _SvcSpec("940359236535", ServiceType.BROADBAND, "SLT BroadBand Service LTE Web Family Plus"),
        ],
        payments=[
            _PmtSpec(date(2024, 2, 16), PaymentMethod.PHYSICAL, _d("5000.00"), "Physical payment"),
        ],
        invoice=_InvSpec(
            number="0038474527-0337",
            balance_bf=_d("7703.28"),
            payments_received=_d("5000.00"),
            charges_total=_d("1559.03"),      # 0+0+1154.84+404.19
            taxes_total=_d("366.21"),
            charges_for_period=_d("1925.24"), # 1559.03+366.21
            total_payable=_d("4628.52"),       # 2703.28+1925.24
            lines=[
                _LineSpec("0359236535",   LineType.RENTAL,
                          "SLT Voice Service 4G Net pal [Rental]",
                          date(2024, 1, 24), date(2024, 2, 16), _d("0.00"), 1),
                _LineSpec("0359236535",   LineType.RENTAL,
                          "SLT Voice Service 4G Net pal [Rental]",
                          date(2024, 2, 17), date(2024, 2, 23), _d("0.00"), 2),
                _LineSpec("940359236535", LineType.RENTAL,
                          "SLT BroadBand Service LTE Web Family Plus [Rental]",
                          date(2024, 1, 24), date(2024, 2, 12), _d("1154.84"), 3),
                _LineSpec("940359236535", LineType.RENTAL,
                          "SLT BroadBand Service LTE Web Family Plus [Rental]",
                          date(2024, 2, 17), date(2024, 2, 23), _d("404.19"), 4),
                _LineSpec(None, LineType.TAX, "Taxes & Levies",
                          None, None, _d("366.21"), 99),
            ],
        ),
    ),

    # ── 2. Single sub-account (Broadband only), partial payment ────────────
    # Check: 2000.00 − 1500.00 + 2070.00 = 2570.00 ✓
    _AcctSpec(
        full_name="Ruwan Jayasinghe",
        address_line1="45 Kandy Road",
        address_line2=None,
        city="Colombo",
        postal_code="10300",
        account_number="002 341 8901",
        telephone_number="0112345678",
        service_label="ADSL service",
        service_accounts=[
            _SvcSpec("0112345678", ServiceType.BROADBAND, "SLT ADSL Service Unlimited"),
        ],
        payments=[
            _PmtSpec(date(2024, 2, 10), PaymentMethod.ONLINE, _d("1500.00"), "Online payment"),
        ],
        invoice=_InvSpec(
            number="0041928374-0201",
            balance_bf=_d("2000.00"),
            payments_received=_d("1500.00"),
            charges_total=_d("1800.00"),
            taxes_total=_d("270.00"),         # 1800 × 0.15
            charges_for_period=_d("2070.00"),
            total_payable=_d("2570.00"),       # 500 arrears + 2070
            lines=[
                _LineSpec("0112345678", LineType.RENTAL,
                          "SLT ADSL Service Unlimited [Rental]",
                          _PERIOD_START, _PERIOD_END, _d("1800.00"), 1),
                _LineSpec(None, LineType.TAX, "Taxes & Levies",
                          None, None, _d("270.00"), 99),
            ],
        ),
    ),

    # ── 3. Three sub-accounts (Voice + Broadband + PeoTV) ──────────────────
    # Check: 3500.00 − 3000.00 + 2530.00 = 3030.00 ✓
    _AcctSpec(
        full_name="Kumari Wickramasinghe",
        address_line1="No 12 Galle Road",
        address_line2="Polhena",
        city="Matara",
        postal_code="81000",
        account_number="003 517 2243",
        telephone_number="0412230011",
        service_label="Fiber service",
        service_accounts=[
            _SvcSpec("0412230011",   ServiceType.VOICE,     "SLT Voice Service"),
            _SvcSpec("940412230011", ServiceType.BROADBAND, "SLT Fiber Broadband 100 Mbps"),
            _SvcSpec("AD1293847",    ServiceType.PEOTV,     "PeoTV Package"),
        ],
        payments=[
            _PmtSpec(date(2024, 2, 12), PaymentMethod.PHYSICAL, _d("3000.00"), "Physical payment"),
        ],
        invoice=_InvSpec(
            number="0052837401-0312",
            balance_bf=_d("3500.00"),
            payments_received=_d("3000.00"),
            charges_total=_d("2200.00"),      # 250 + 1500 + 450
            taxes_total=_d("330.00"),         # 2200 × 0.15
            charges_for_period=_d("2530.00"),
            total_payable=_d("3030.00"),       # 500 arrears + 2530
            lines=[
                _LineSpec("0412230011",   LineType.RENTAL, "SLT Voice Service [Rental]",
                          _PERIOD_START, _PERIOD_END, _d("250.00"), 1),
                _LineSpec("940412230011", LineType.RENTAL, "SLT Fiber Broadband 100 Mbps [Rental]",
                          _PERIOD_START, _PERIOD_END, _d("1500.00"), 2),
                _LineSpec("AD1293847",    LineType.RENTAL, "PeoTV Package [Rental]",
                          _PERIOD_START, _PERIOD_END, _d("450.00"), 3),
                _LineSpec(None, LineType.TAX, "Taxes & Levies",
                          None, None, _d("330.00"), 99),
            ],
        ),
    ),

    # ── 4. Negative DISCOUNT line ──────────────────────────────────────────
    # Rental 2500 − discount 250 = charges_total 2250; tax on net = 337.50.
    # Check: 2000.00 − 2000.00 + 2587.50 = 2587.50 ✓
    _AcctSpec(
        full_name="Sanath Perera",
        address_line1="88 Main Street",
        address_line2=None,
        city="Kurunegala",
        postal_code="60000",
        account_number="005 821 3344",
        telephone_number="0372244556",
        service_label="LTE service",
        service_accounts=[
            _SvcSpec("0372244556", ServiceType.BROADBAND, "SLT LTE Home Broadband"),
        ],
        payments=[
            _PmtSpec(date(2024, 2, 8), PaymentMethod.CARD, _d("2000.00"), "Card payment"),
        ],
        invoice=_InvSpec(
            number="0067483920-0422",
            balance_bf=_d("2000.00"),
            payments_received=_d("2000.00"),
            charges_total=_d("2250.00"),      # 2500 + (−250)
            taxes_total=_d("337.50"),         # 2250 × 0.15
            charges_for_period=_d("2587.50"),
            total_payable=_d("2587.50"),       # 0 arrears + 2587.50
            lines=[
                _LineSpec("0372244556", LineType.RENTAL,
                          "SLT LTE Home Broadband [Rental]",
                          _PERIOD_START, _PERIOD_END, _d("2500.00"), 1),
                _LineSpec("0372244556", LineType.DISCOUNT,
                          "Loyalty discount",
                          None, None, _d("-250.00"), 2),
                _LineSpec(None, LineType.TAX, "Taxes & Levies",
                          None, None, _d("337.50"), 99),
            ],
        ),
    ),

    # ── 5. Zero balance — no charges, no arrears ───────────────────────────
    # Exercises BILLING.md §7 "zero charges" edge case (no line items).
    # Check: 0 − 0 + 0 = 0.00 ✓
    _AcctSpec(
        full_name="Nimal Fernando",
        address_line1="23 Hospital Road",
        address_line2=None,
        city="Galle",
        postal_code="80000",
        account_number="006 193 7712",
        telephone_number="0912345900",
        service_label="ADSL service",
        service_accounts=[
            _SvcSpec("0912345900", ServiceType.BROADBAND, "SLT ADSL Basic"),
        ],
        payments=[],
        invoice=_InvSpec(
            number="0073920183-0524",
            balance_bf=_d("0.00"),
            payments_received=_d("0.00"),
            charges_total=_d("0.00"),
            taxes_total=_d("0.00"),
            charges_for_period=_d("0.00"),
            total_payable=_d("0.00"),
            lines=[],   # zero-charge period — no line items
        ),
    ),

    # ── 6. Carried arrears — no payment received, OVERDUE ─────────────────
    # Exercises BILLING.md §7 "no payments → arrears = balance_bf".
    # Check: 3200.00 − 0.00 + 2070.00 = 5270.00 ✓
    _AcctSpec(
        full_name="Dilrukshi Amarasinghe",
        address_line1="15 Rajapaksha Road",
        address_line2=None,
        city="Kandy",
        postal_code="20000",
        account_number="007 448 0912",
        telephone_number="0812890034",
        service_label="ADSL service",
        service_accounts=[
            _SvcSpec("0812890034", ServiceType.BROADBAND, "SLT ADSL Unlimited Plus"),
        ],
        payments=[],   # no payment this period
        invoice=_InvSpec(
            number="0084729301-0634",
            balance_bf=_d("3200.00"),
            payments_received=_d("0.00"),
            charges_total=_d("1800.00"),
            taxes_total=_d("270.00"),         # 1800 × 0.15
            charges_for_period=_d("2070.00"),
            total_payable=_d("5270.00"),       # 3200 arrears + 2070
            status=InvoiceStatus.OVERDUE,
            lines=[
                _LineSpec("0812890034", LineType.RENTAL,
                          "SLT ADSL Unlimited Plus [Rental]",
                          _PERIOD_START, _PERIOD_END, _d("1800.00"), 1),
                _LineSpec(None, LineType.TAX, "Taxes & Levies",
                          None, None, _d("270.00"), 99),
            ],
        ),
    ),

    # ── 7. Two sub-accounts (Broadband + PeoTV) ────────────────────────────
    # Check: 4500.00 − 4000.00 + 3910.00 = 4410.00 ✓
    _AcctSpec(
        full_name="Anura Dissanayake",
        address_line1="67 Baseline Road",
        address_line2=None,
        city="Colombo",
        postal_code="10500",
        account_number="008 234 5567",
        telephone_number="0113344556",
        service_label="Fiber service",
        service_accounts=[
            _SvcSpec("0113344556", ServiceType.BROADBAND, "SLT Fiber Broadband 50 Mbps"),
            _SvcSpec("AD7382910",  ServiceType.PEOTV,     "PeoTV Plus"),
        ],
        payments=[
            _PmtSpec(date(2024, 2, 14), PaymentMethod.ONLINE, _d("4000.00"), "Online payment"),
        ],
        invoice=_InvSpec(
            number="0095827304-0712",
            balance_bf=_d("4500.00"),
            payments_received=_d("4000.00"),
            charges_total=_d("3400.00"),      # 2800 + 600
            taxes_total=_d("510.00"),         # 3400 × 0.15
            charges_for_period=_d("3910.00"),
            total_payable=_d("4410.00"),       # 500 arrears + 3910
            lines=[
                _LineSpec("0113344556", LineType.RENTAL,
                          "SLT Fiber Broadband 50 Mbps [Rental]",
                          _PERIOD_START, _PERIOD_END, _d("2800.00"), 1),
                _LineSpec("AD7382910",  LineType.RENTAL,
                          "PeoTV Plus [Rental]",
                          _PERIOD_START, _PERIOD_END, _d("600.00"), 2),
                _LineSpec(None, LineType.TAX, "Taxes & Levies",
                          None, None, _d("510.00"), 99),
            ],
        ),
    ),

    # ── 8. Single sub-account (Voice only), exact payment — zero arrears ───
    # Check: 500.00 − 500.00 + 402.50 = 402.50 ✓
    _AcctSpec(
        full_name="Thilini Rathnayake",
        address_line1="34 Temple Road",
        address_line2=None,
        city="Negombo",
        postal_code="11500",
        account_number="009 876 1234",
        telephone_number="0312567890",
        service_label="Voice service",
        service_accounts=[
            _SvcSpec("0312567890", ServiceType.VOICE, "SLT Voice Local"),
        ],
        payments=[
            _PmtSpec(date(2024, 2, 11), PaymentMethod.PHYSICAL, _d("500.00"), "Physical payment"),
        ],
        invoice=_InvSpec(
            number="0106748291-0823",
            balance_bf=_d("500.00"),
            payments_received=_d("500.00"),
            charges_total=_d("350.00"),
            taxes_total=_d("52.50"),          # 350 × 0.15
            charges_for_period=_d("402.50"),
            total_payable=_d("402.50"),        # 0 arrears + 402.50
            lines=[
                _LineSpec("0312567890", LineType.RENTAL, "SLT Voice Local [Rental]",
                          _PERIOD_START, _PERIOD_END, _d("350.00"), 1),
                _LineSpec(None, LineType.TAX, "Taxes & Levies",
                          None, None, _d("52.50"), 99),
            ],
        ),
    ),
]


# ---------------------------------------------------------------------------
# Insertion helpers
# ---------------------------------------------------------------------------

def _exists(session: Session, account_number: str) -> bool:
    return session.scalar(
        select(Account.id).where(Account.account_number == account_number)
    ) is not None


def _insert_one(session: Session, spec: _AcctSpec) -> None:
    """Insert one account and all related rows. Caller commits."""
    customer = Customer(
        full_name=spec.full_name,
        address_line1=spec.address_line1,
        address_line2=spec.address_line2,
        city=spec.city,
        postal_code=spec.postal_code,
        status=AccountStatus.ACTIVE,
    )
    session.add(customer)
    session.flush()  # populate customer.id

    account = Account(
        customer_id=customer.id,
        account_number=spec.account_number,
        telephone_number=spec.telephone_number,
        service_label=spec.service_label,
        status=AccountStatus.ACTIVE,
    )
    session.add(account)
    session.flush()  # populate account.id

    # Build service_number → DB id map for line-item wiring
    svc_id: dict[str, int] = {}
    for sv in spec.service_accounts:
        sa_row = ServiceAccount(
            account_id=account.id,
            service_number=sv.number,
            service_type=sv.stype,
            label=sv.label,
        )
        session.add(sa_row)
        session.flush()
        svc_id[sv.number] = sa_row.id

    for pmt in spec.payments:
        session.add(Payment(
            account_id=account.id,
            payment_date=pmt.payment_date,
            method=pmt.method,
            amount=pmt.amount,
            reference=pmt.reference,
        ))

    if spec.invoice is None:
        return

    inv = Invoice(
        account_id=account.id,
        invoice_number=spec.invoice.number,
        billing_date=_BILLING_DATE,
        period_start=_PERIOD_START,
        period_end=_PERIOD_END,
        due_date=_DUE_DATE,
        balance_bf=spec.invoice.balance_bf,
        payments_received=spec.invoice.payments_received,
        charges_total=spec.invoice.charges_total,
        taxes_total=spec.invoice.taxes_total,
        charges_for_period=spec.invoice.charges_for_period,
        total_payable=spec.invoice.total_payable,
        status=spec.invoice.status,
    )
    session.add(inv)
    session.flush()  # populate inv.id

    for line in spec.invoice.lines:
        sa_fk = svc_id.get(line.svc_number) if line.svc_number else None
        session.add(InvoiceLineItem(
            invoice_id=inv.id,
            service_account_id=sa_fk,
            line_type=line.ltype,
            description=line.description,
            period_start=line.period_start,
            period_end=line.period_end,
            amount=line.amount,
            sort_order=line.sort_order,
        ))


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def main() -> None:
    configure_logging()
    log.info("seeding database …")

    inserted = skipped = errors = 0

    with SessionLocal() as session:
        for spec in _ACCOUNTS:
            if _exists(session, spec.account_number):
                log.debug("skip  %-20s (already exists)", spec.account_number)
                skipped += 1
                continue
            try:
                _insert_one(session, spec)
                session.commit()
                log.info("seed  %-20s %s", spec.account_number, spec.full_name)
                inserted += 1
            except Exception:
                session.rollback()
                log.exception("FAIL  %s", spec.account_number)
                errors += 1

    log.info(
        "done — %d inserted, %d skipped, %d error(s)",
        inserted, skipped, errors,
    )
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
