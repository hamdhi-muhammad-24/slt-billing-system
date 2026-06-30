"""
Synthetic seed data for the SLT e-bill system.

Usage:  python -m app.db.seed
Idempotent — accounts already present (matched by account_number) are skipped.
All monetary values are Decimal; no float arithmetic anywhere.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.security import hash_password
from app.core.logging import configure_logging, get_logger
from app.db.base import SessionLocal
from app.db.models import (
    Account,
    AccountStatus,
    AddressType,
    BillDeliveryMethod,
    BillingPeriod,
    ConnectionType,
    Customer,
    CustomerAddress,
    CustomerType,
    DailyUsageRecord,
    Invoice,
    InvoiceLineItem,
    InvoiceStatus,
    LineType,
    Package,
    Payment,
    PaymentMethod,
    PaymentStatus,
    ServiceAddon,
    ServiceAccount,
    ServiceType,
    UsageSummary,
    UserRole,
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

    # ── 1. Sample-1 — Voice + Broadband, split-period rentals + excess usage ─
    # Check: 7703.28 − 5000.00 + 2080.48 = 4783.76 ✓
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
            charges_total=_d("1809.03"),      # 0+0+1154.84+404.19+250.00
            taxes_total=_d("271.45"),         # 1809.03×0.15
            charges_for_period=_d("2080.48"), # 1809.03+271.45
            total_payable=_d("4783.76"),       # 2703.28+2080.48
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
                _LineSpec("940359236535", LineType.USAGE,
                          "Broadband excess usage",
                          _PERIOD_START, _PERIOD_END, _d("250.00"), 5),
                _LineSpec(None, LineType.TAX, "Taxes & Levies",
                          None, None, _d("271.45"), 99),
            ],
        ),
    ),

    # ── 2. Single sub-account (Broadband only), partial payment ────────────
    # Check: 2000.00 − 1500.00 + 2990.00 = 3490.00 ✓
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
            charges_total=_d("2600.00"),      # 1800+250+500+150-100
            taxes_total=_d("390.00"),         # 2600×0.15
            charges_for_period=_d("2990.00"),
            total_payable=_d("3490.00"),       # 500 arrears + 2990
            lines=[
                _LineSpec("0112345678", LineType.RENTAL,
                          "SLT ADSL Service Unlimited [Rental]",
                          _PERIOD_START, _PERIOD_END, _d("1800.00"), 1),
                _LineSpec("0112345678", LineType.USAGE,
                          "Broadband excess usage",
                          _PERIOD_START, _PERIOD_END, _d("250.00"), 2),
                _LineSpec("0112345678", LineType.FEE,
                          "Static IP address",
                          None, None, _d("500.00"), 3),
                _LineSpec("0112345678", LineType.FEE,
                          "Modem rental",
                          None, None, _d("150.00"), 4),
                _LineSpec("0112345678", LineType.DISCOUNT,
                          "Promotional discount",
                          None, None, _d("-100.00"), 5),
                _LineSpec(None, LineType.TAX, "Taxes & Levies",
                          None, None, _d("390.00"), 99),
            ],
        ),
    ),

    # ── 3. Three sub-accounts (Voice + Broadband + PeoTV) ──────────────────
    # Check: 3500.00 − 3000.00 + 2760.00 = 3260.00 ✓
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
            charges_total=_d("2400.00"),      # 250+1500+200+450
            taxes_total=_d("360.00"),         # 2400×0.15
            charges_for_period=_d("2760.00"),
            total_payable=_d("3260.00"),       # 500 arrears + 2760
            lines=[
                _LineSpec("0412230011",   LineType.RENTAL, "SLT Voice Service [Rental]",
                          _PERIOD_START, _PERIOD_END, _d("250.00"), 1),
                _LineSpec("940412230011", LineType.RENTAL, "SLT Fiber Broadband 100 Mbps [Rental]",
                          _PERIOD_START, _PERIOD_END, _d("1500.00"), 2),
                _LineSpec("940412230011", LineType.USAGE, "Broadband excess usage",
                          _PERIOD_START, _PERIOD_END, _d("200.00"), 3),
                _LineSpec("AD1293847",    LineType.RENTAL, "PeoTV Package [Rental]",
                          _PERIOD_START, _PERIOD_END, _d("450.00"), 4),
                _LineSpec(None, LineType.TAX, "Taxes & Levies",
                          None, None, _d("360.00"), 99),
            ],
        ),
    ),

    # ── 4. Negative DISCOUNT line ──────────────────────────────────────────
    # LTE rental + usage + fees − discount = 2980; tax = 447.
    # Check: 2000.00 − 2000.00 + 3427.00 = 3427.00 ✓
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
            charges_total=_d("2980.00"),      # 2500+180+350+200-250
            taxes_total=_d("447.00"),         # 2980×0.15
            charges_for_period=_d("3427.00"),
            total_payable=_d("3427.00"),       # 0 arrears + 3427
            lines=[
                _LineSpec("0372244556", LineType.RENTAL,
                          "SLT LTE Home Broadband [Rental]",
                          _PERIOD_START, _PERIOD_END, _d("2500.00"), 1),
                _LineSpec("0372244556", LineType.USAGE,
                          "Broadband excess usage",
                          _PERIOD_START, _PERIOD_END, _d("180.00"), 2),
                _LineSpec("0372244556", LineType.FEE,
                          "Static IP address",
                          None, None, _d("350.00"), 3),
                _LineSpec("0372244556", LineType.FEE,
                          "Router rental",
                          None, None, _d("200.00"), 4),
                _LineSpec("0372244556", LineType.DISCOUNT,
                          "Loyalty discount",
                          None, None, _d("-250.00"), 5),
                _LineSpec(None, LineType.TAX, "Taxes & Levies",
                          None, None, _d("447.00"), 99),
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
    # Check: 3200.00 − 0.00 + 2817.50 = 6017.50 ✓
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
            charges_total=_d("2450.00"),      # 1800+350+250+150-100
            taxes_total=_d("367.50"),         # 2450×0.15
            charges_for_period=_d("2817.50"),
            total_payable=_d("6017.50"),       # 3200 arrears + 2817.50
            status=InvoiceStatus.OVERDUE,
            lines=[
                _LineSpec("0812890034", LineType.RENTAL,
                          "SLT ADSL Unlimited Plus [Rental]",
                          _PERIOD_START, _PERIOD_END, _d("1800.00"), 1),
                _LineSpec("0812890034", LineType.USAGE,
                          "Broadband excess usage",
                          _PERIOD_START, _PERIOD_END, _d("350.00"), 2),
                _LineSpec("0812890034", LineType.FEE,
                          "Late payment fee",
                          None, None, _d("250.00"), 3),
                _LineSpec("0812890034", LineType.FEE,
                          "Reconnection fee",
                          None, None, _d("150.00"), 4),
                _LineSpec("0812890034", LineType.DISCOUNT,
                          "Waiver adjustment",
                          None, None, _d("-100.00"), 5),
                _LineSpec(None, LineType.TAX, "Taxes & Levies",
                          None, None, _d("367.50"), 99),
            ],
        ),
    ),

    # ── 7. Two sub-accounts (Broadband + PeoTV) ────────────────────────────
    # Check: 4500.00 − 4000.00 + 4450.50 = 4950.50 ✓
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
            charges_total=_d("3870.00"),      # 2800+320+600+150
            taxes_total=_d("580.50"),         # 3870×0.15
            charges_for_period=_d("4450.50"),
            total_payable=_d("4950.50"),       # 500 arrears + 4450.50
            lines=[
                _LineSpec("0113344556", LineType.RENTAL,
                          "SLT Fiber Broadband 50 Mbps [Rental]",
                          _PERIOD_START, _PERIOD_END, _d("2800.00"), 1),
                _LineSpec("0113344556", LineType.USAGE,
                          "Broadband excess usage",
                          _PERIOD_START, _PERIOD_END, _d("320.00"), 2),
                _LineSpec("AD7382910",  LineType.RENTAL,
                          "PeoTV Plus [Rental]",
                          _PERIOD_START, _PERIOD_END, _d("600.00"), 3),
                _LineSpec("AD7382910",  LineType.FEE,
                          "PeoTV HD decoder rental",
                          None, None, _d("150.00"), 4),
                _LineSpec(None, LineType.TAX, "Taxes & Levies",
                          None, None, _d("580.50"), 99),
            ],
        ),
    ),

    # ── 8. Single sub-account (Voice only), exact payment — zero arrears ───
    # Check: 500.00 − 500.00 + 885.50 = 885.50 ✓
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
            charges_total=_d("770.00"),       # 350+120+280+50-30
            taxes_total=_d("115.50"),         # 770×0.15
            charges_for_period=_d("885.50"),
            total_payable=_d("885.50"),        # 0 arrears + 885.50
            lines=[
                _LineSpec("0312567890", LineType.RENTAL, "SLT Voice Local [Rental]",
                          _PERIOD_START, _PERIOD_END, _d("350.00"), 1),
                _LineSpec("0312567890", LineType.USAGE, "Local call charges",
                          _PERIOD_START, _PERIOD_END, _d("120.00"), 2),
                _LineSpec("0312567890", LineType.USAGE, "IDD call charges",
                          _PERIOD_START, _PERIOD_END, _d("280.00"), 3),
                _LineSpec("0312567890", LineType.FEE, "Caller ID service",
                          None, None, _d("50.00"), 4),
                _LineSpec("0312567890", LineType.DISCOUNT, "Loyalty discount",
                          None, None, _d("-30.00"), 5),
                _LineSpec(None, LineType.TAX, "Taxes & Levies",
                          None, None, _d("115.50"), 99),
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
# Realistic SLT-style enrichment dataset
# ---------------------------------------------------------------------------

_PACKAGES = [
    ("VOICE-LOCAL", "SLT Voice Local", ServiceType.VOICE, _d("350.00"), None, None, _d("0.00")),
    ("ADSL-BASIC", "SLT ADSL Basic", ServiceType.BROADBAND, _d("1800.00"), "16 Mbps", _d("120.00"), _d("45.00")),
    ("LTE-WEB-FAMILY", "SLT LTE Web Family Plus", ServiceType.BROADBAND, _d("2500.00"), "LTE", _d("160.00"), _d("50.00")),
    ("FIBER-50", "SLT Fiber Broadband 50 Mbps", ServiceType.BROADBAND, _d("2800.00"), "50 Mbps", _d("300.00"), _d("40.00")),
    ("FIBER-100", "SLT Fiber Broadband 100 Mbps", ServiceType.BROADBAND, _d("3900.00"), "100 Mbps", _d("500.00"), _d("35.00")),
    ("PEOTV-PLUS", "PeoTV Plus", ServiceType.PEOTV, _d("600.00"), None, None, _d("0.00")),
]

_CUSTOMER_PROFILES = [
    ("Mr", "Kasun", "Perera", "199012345678", "kasun.perera@slt-demo.lk", "0712456789", "Colombo", "Western", "10100"),
    ("Ms", "Ishara", "Fernando", "198875432109", "ishara.fernando@slt-demo.lk", "0723344556", "Gampaha", "Western", "11000"),
    ("Mrs", "Chamari", "Silva", "197765432198", "chamari.silva@slt-demo.lk", "0771122334", "Kalutara", "Western", "12000"),
    ("Mr", "Dinesh", "Bandara", "199334455667", "dinesh.bandara@slt-demo.lk", "0769988776", "Kandy", "Central", "20000"),
    ("Ms", "Nadeesha", "Herath", "198456789012", "nadeesha.herath@slt-demo.lk", "0701234567", "Matale", "Central", "21000"),
    ("Mr", "Sajith", "Ekanayake", "197912345679", "sajith.ekanayake@slt-demo.lk", "0754443322", "Nuwara Eliya", "Central", "22200"),
    ("Mrs", "Anjali", "Gunasekara", "199145678901", "anjali.gunasekara@slt-demo.lk", "0717788990", "Galle", "Southern", "80000"),
    ("Mr", "Roshan", "Jayawardena", "198223456789", "roshan.jaya@slt-demo.lk", "0726677889", "Matara", "Southern", "81000"),
    ("Ms", "Malsha", "Abeywickrama", "199556789123", "malsha.abey@slt-demo.lk", "0782255889", "Hambantota", "Southern", "82000"),
    ("Mr", "Lahiru", "Wijesinghe", "198998765432", "lahiru.wije@slt-demo.lk", "0744455667", "Kurunegala", "North Western", "60000"),
    ("Mrs", "Dinithi", "Ranaweera", "197856781234", "dinithi.rana@slt-demo.lk", "0719090901", "Puttalam", "North Western", "61300"),
    ("Mr", "Heshan", "Madushanka", "199667891234", "heshan.madu@slt-demo.lk", "0778899001", "Anuradhapura", "North Central", "50000"),
    ("Ms", "Tharushi", "Samarasinghe", "200012345678", "tharushi.samara@slt-demo.lk", "0761010102", "Polonnaruwa", "North Central", "51000"),
    ("Mr", "Pradeep", "Karunaratne", "198734567890", "pradeep.karu@slt-demo.lk", "0756767676", "Badulla", "Uva", "90000"),
    ("Mrs", "Sanduni", "Amarasekara", "199078901234", "sanduni.ama@slt-demo.lk", "0715656565", "Monaragala", "Uva", "91000"),
    ("Mr", "Akila", "Senanayake", "198645678901", "akila.sena@slt-demo.lk", "0724545454", "Ratnapura", "Sabaragamuwa", "70000"),
    ("Ms", "Madhavi", "Pathirana", "199789012345", "madhavi.path@slt-demo.lk", "0773434343", "Kegalle", "Sabaragamuwa", "71000"),
    ("Mr", "Yohan", "Rodrigo", "198512349876", "yohan.rodrigo@slt-demo.lk", "0707878787", "Jaffna", "Northern", "40000"),
    ("Mrs", "Kavindya", "Premaratne", "199201234567", "kavindya.prema@slt-demo.lk", "0762323232", "Batticaloa", "Eastern", "30000"),
    ("Mr", "Milan", "Dias", "198901234568", "milan.dias@slt-demo.lk", "0712121212", "Trincomalee", "Eastern", "31000"),
]

_PERIODS_2026 = [
    ("2026-01", date(2026, 1, 1), date(2026, 1, 31), date(2026, 2, 1), date(2026, 2, 21)),
    ("2026-02", date(2026, 2, 1), date(2026, 2, 28), date(2026, 3, 1), date(2026, 3, 21)),
    ("2026-03", date(2026, 3, 1), date(2026, 3, 31), date(2026, 4, 1), date(2026, 4, 21)),
    ("2026-04", date(2026, 4, 1), date(2026, 4, 30), date(2026, 5, 1), date(2026, 5, 21)),
    ("2026-05", date(2026, 5, 1), date(2026, 5, 31), date(2026, 6, 1), date(2026, 6, 21)),
    ("2026-06", date(2026, 6, 1), date(2026, 6, 30), date(2026, 7, 1), date(2026, 7, 21)),
]


def _address_text(customer: Customer) -> str:
    return ", ".join(
        p for p in [customer.address_line1, customer.address_line2, customer.city, customer.postal_code] if p
    )


def _first_last(full_name: str) -> tuple[str | None, str | None]:
    parts = full_name.split()
    if len(parts) == 1:
        return parts[0], None
    return (parts[0], parts[-1]) if parts else (None, None)


def _package_map(session: Session) -> dict[str, Package]:
    packages: dict[str, Package] = {}
    for code, name, stype, monthly_fee, speed, data_limit, extra_rate in _PACKAGES:
        pkg = session.scalar(select(Package).where(Package.package_code == code))
        if pkg is None:
            pkg = Package(package_code=code, name=name, service_type=stype)
            session.add(pkg)
            session.flush()
        pkg.monthly_fee = monthly_fee
        pkg.speed_tier = speed
        pkg.data_limit_gb = data_limit
        pkg.anytime_gb = data_limit
        pkg.extra_charge_per_gb = extra_rate
        pkg.included_voice_minutes = _d("250.000") if stype == ServiceType.VOICE else None
        pkg.active_from = date(2026, 1, 1)
        pkg.tax_applicable = True
        pkg.is_active = True
        packages[code] = pkg
    return packages


def _period_map(session: Session) -> dict[str, BillingPeriod]:
    periods: dict[str, BillingPeriod] = {}
    for code, start, end, billing_date, due_date in [("2024-01", _PERIOD_START, _PERIOD_END, _BILLING_DATE, _DUE_DATE), *_PERIODS_2026]:
        row = session.scalar(select(BillingPeriod).where(BillingPeriod.code == code))
        if row is None:
            row = BillingPeriod(code=code, period_start=start, period_end=end, billing_date=billing_date, due_date=due_date)
            session.add(row)
            session.flush()
        periods[code] = row
    return periods


def _ensure_address(session: Session, customer: Customer, province: str | None = None) -> CustomerAddress:
    existing = session.scalar(
        select(CustomerAddress).where(
            CustomerAddress.customer_id == customer.id,
            CustomerAddress.address_type == AddressType.BILLING,
        )
    )
    if existing is not None:
        return existing
    address = CustomerAddress(
        customer_id=customer.id,
        address_type=AddressType.BILLING,
        line1=customer.address_line1 or "Address not recorded",
        line2=customer.address_line2,
        city=customer.city,
        district=customer.city,
        province=province,
        postal_code=customer.postal_code,
        country="Sri Lanka",
        is_primary=True,
    )
    session.add(address)
    session.flush()
    return address


def _upsert_customer_user(session: Session, customer: Customer, email: str) -> None:
    user = session.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            email=email,
            password_hash=hash_password("Cust@2026!Demo"),
            role=UserRole.CUSTOMER,
            is_active=True,
        )
        session.add(user)
        session.flush()
    customer.user_id = customer.user_id or user.id


def _connection_for(stype: ServiceType, package_code: str) -> ConnectionType:
    if stype == ServiceType.VOICE:
        return ConnectionType.VOICE
    if stype == ServiceType.PEOTV:
        return ConnectionType.PEOTV
    if package_code.startswith("FIBER"):
        return ConnectionType.FTTH
    if package_code.startswith("LTE"):
        return ConnectionType.LTE
    return ConnectionType.ADSL


def _service_package_code(service: ServiceAccount, account: Account, sequence: int = 0) -> str:
    if service.service_type == ServiceType.VOICE:
        return "VOICE-LOCAL"
    if service.service_type == ServiceType.PEOTV:
        return "PEOTV-PLUS"
    label = (service.label or account.service_label or "").upper()
    if "FIBER" in label and "100" in label:
        return "FIBER-100"
    if "FIBER" in label:
        return "FIBER-50"
    if "LTE" in label:
        return "LTE-WEB-FAMILY"
    return "ADSL-BASIC" if sequence % 2 == 0 else "FIBER-50"


def _enrich_existing_seed_rows(session: Session, packages: dict[str, Package]) -> None:
    existing_contacts = [
        ("199912345678", "pavithim@slt-customer.lk", "0711001001", "Uva"),
        ("198812345678", "ruwan@slt-customer.lk", "0711001002", "Western"),
        ("197712345678", "kumari@slt-customer.lk", "0711001003", "Southern"),
        ("199412345678", "sanath@slt-customer.lk", "0711001004", "North Western"),
        ("198512345678", "nimal@slt-customer.lk", "0711001005", "Southern"),
        ("197612345678", "dilrukshi@slt-customer.lk", "0711001006", "Central"),
        ("199712345678", "anura@slt-customer.lk", "0711001007", "Western"),
        ("198212345678", "thilini@slt-customer.lk", "0711001008", "Western"),
    ]
    customers = session.scalars(select(Customer).order_by(Customer.id).limit(8)).all()
    for customer, (nic, email, mobile, province) in zip(customers, existing_contacts):
        first_name, last_name = _first_last(customer.full_name)
        customer.nic = customer.nic or nic
        customer.title = customer.title or "Mr"
        customer.first_name = customer.first_name or first_name
        customer.last_name = customer.last_name or last_name
        customer.email = customer.email or email
        customer.mobile_number = customer.mobile_number or mobile
        customer.preferred_language = customer.preferred_language or "en"
        customer.customer_type = customer.customer_type or CustomerType.RESIDENTIAL
        _upsert_customer_user(session, customer, email)
        address = _ensure_address(session, customer, province)
        accounts = session.scalars(select(Account).where(Account.customer_id == customer.id)).all()
        for account in accounts:
            account.billing_cycle = account.billing_cycle or "MONTHLY_25"
            account.bill_delivery_method = account.bill_delivery_method or BillDeliveryMethod.PORTAL
            account.credit_limit = account.credit_limit or _d("25000.00")
            account.deposit_amount = account.deposit_amount or _d("1000.00")
            account.opened_on = account.opened_on or date(2023, 1, 1)
            account.notify_email = True
            account.notify_sms = True
            services = session.scalars(
                select(ServiceAccount).where(ServiceAccount.account_id == account.id).order_by(ServiceAccount.id)
            ).all()
            for i, service in enumerate(services):
                code = _service_package_code(service, account, i)
                service.package_id = service.package_id or packages[code].id
                service.installation_address_id = service.installation_address_id or address.id
                service.connection_type = service.connection_type or _connection_for(service.service_type, code)
                service.activated_on = service.activated_on or date(2023, 1, 15)
                service.contract_number = service.contract_number or f"CTR-{account.account_number.replace(' ', '')}-{i + 1}"
                if service.service_type == ServiceType.BROADBAND:
                    service.service_username = service.service_username or f"{account.account_number.replace(' ', '')}@sltbb"


def _create_realistic_customers(session: Session, packages: dict[str, Package]) -> None:
    for idx, (title, first, last, nic, email, mobile, city, province, postal) in enumerate(_CUSTOMER_PROFILES, start=1):
        if session.scalar(select(Customer.id).where(Customer.nic == nic)) is not None:
            continue
        customer = Customer(
            full_name=f"{first} {last}",
            nic=nic,
            title=title,
            first_name=first,
            last_name=last,
            email=email,
            mobile_number=mobile,
            alternate_phone=f"011{idx:07d}",
            preferred_language="en",
            date_of_birth=date(1980 + (idx % 18), ((idx - 1) % 12) + 1, min(idx, 28)),
            customer_type=CustomerType.RESIDENTIAL if idx % 5 else CustomerType.BUSINESS,
            address_line1=f"No {20 + idx}, Demo Road",
            address_line2=f"{city} Town",
            city=city,
            postal_code=postal,
            status=AccountStatus.SUSPENDED if idx == 6 else AccountStatus.ACTIVE,
        )
        session.add(customer)
        session.flush()
        _upsert_customer_user(session, customer, email)
        address = _ensure_address(session, customer, province)

        account = Account(
            customer_id=customer.id,
            account_number=f"02{idx:02d} {345 + idx:03d} {7800 + idx:04d}",
            telephone_number=f"0{10 + (idx % 8)}{2200000 + idx:07d}"[:10],
            service_label=("Fiber service" if idx % 3 == 0 else "LTE service" if idx % 4 == 0 else "ADSL service"),
            billing_cycle="MONTHLY_01",
            bill_delivery_method=BillDeliveryMethod.PORTAL,
            credit_limit=_d("30000.00"),
            deposit_amount=_d("1500.00"),
            opened_on=date(2025, ((idx - 1) % 12) + 1, 1),
            notify_email=True,
            notify_sms=True,
            status=AccountStatus.SUSPENDED if idx == 6 else AccountStatus.ACTIVE,
        )
        session.add(account)
        session.flush()

        if idx % 7 == 0:
            specs = [(account.telephone_number, ServiceType.VOICE, "SLT Voice Local", "VOICE-LOCAL")]
        elif idx % 5 == 0:
            specs = [
                (account.telephone_number, ServiceType.BROADBAND, "SLT Fiber Broadband 100 Mbps", "FIBER-100"),
                (f"AD{idx:07d}", ServiceType.PEOTV, "PeoTV Plus", "PEOTV-PLUS"),
            ]
        elif idx % 3 == 0:
            specs = [
                (account.telephone_number, ServiceType.VOICE, "SLT Voice Service", "VOICE-LOCAL"),
                (f"94{account.telephone_number[1:]}", ServiceType.BROADBAND, "SLT Fiber Broadband 50 Mbps", "FIBER-50"),
                (f"AD{idx:07d}", ServiceType.PEOTV, "PeoTV Plus", "PEOTV-PLUS"),
            ]
        elif idx % 4 == 0:
            specs = [(f"94{account.telephone_number[1:]}", ServiceType.BROADBAND, "SLT LTE Web Family Plus", "LTE-WEB-FAMILY")]
        else:
            specs = [(account.telephone_number, ServiceType.BROADBAND, "SLT ADSL Basic", "ADSL-BASIC")]

        for svc_idx, (number, stype, label, code) in enumerate(specs, start=1):
            session.add(ServiceAccount(
                account_id=account.id,
                package_id=packages[code].id,
                installation_address_id=address.id,
                service_number=number,
                service_type=stype,
                connection_type=_connection_for(stype, code),
                label=label,
                activated_on=account.opened_on,
                contract_number=f"CTR-{account.account_number.replace(' ', '')}-{svc_idx}",
                router_serial=f"RTR{idx:03d}{svc_idx:02d}" if stype == ServiceType.BROADBAND else None,
                ont_serial=f"ONT{idx:03d}{svc_idx:02d}" if code.startswith("FIBER") else None,
                service_username=f"{number}@sltbb" if stype == ServiceType.BROADBAND else None,
                status=account.status,
            ))


def _invoice_exists(session: Session, account_id: int, start: date, end: date) -> bool:
    return session.scalar(
        select(Invoice.id).where(
            Invoice.account_id == account_id,
            Invoice.period_start == start,
            Invoice.period_end == end,
        )
    ) is not None


def _service_charge(service: ServiceAccount, package: Package, month_index: int, account_index: int) -> tuple[Decimal, Decimal]:
    rental = Decimal(package.monthly_fee or 0)
    usage_charge = _d("0.00")
    if service.service_type == ServiceType.BROADBAND:
        included = Decimal(package.data_limit_gb or package.anytime_gb or 0)
        used = included * (Decimal("0.55") + Decimal((month_index + account_index) % 7) / Decimal("20"))
        overage = max(_d("0.000"), used - included)
        usage_charge = (overage * Decimal(package.extra_charge_per_gb or 0)).quantize(Decimal("0.01"))
    return rental, usage_charge


def _upsert_usage(
    session: Session,
    service: ServiceAccount,
    package: Package,
    period: BillingPeriod,
    month_index: int,
    account_index: int,
    usage_charge: Decimal,
) -> None:
    if service.service_type != ServiceType.BROADBAND:
        return
    if session.scalar(
        select(UsageSummary.id).where(
            UsageSummary.service_account_id == service.id,
            UsageSummary.billing_period_id == period.id,
            UsageSummary.metric == "data_gb",
        )
    ) is not None:
        return
    included = Decimal(package.data_limit_gb or package.anytime_gb or 0)
    used = (included * (Decimal("0.55") + Decimal((month_index + account_index) % 7) / Decimal("20"))).quantize(Decimal("0.001"))
    overage = max(_d("0.000"), used - included)
    remaining = max(_d("0.000"), included - used)
    session.add(UsageSummary(
        service_account_id=service.id,
        billing_period_id=period.id,
        period_start=period.period_start,
        period_end=period.period_end,
        metric="data_gb",
        included_quantity=included,
        used_quantity=used,
        remaining_quantity=remaining,
        overage_quantity=overage,
        charge=usage_charge,
    ))
    days = (period.period_end - period.period_start).days + 1
    daily_total = (used / Decimal(days)).quantize(Decimal("0.001"))
    for day in range(days):
        usage_date = period.period_start + timedelta(days=day)
        session.add(DailyUsageRecord(
            service_account_id=service.id,
            billing_period_id=period.id,
            usage_date=usage_date,
            bucket="ANYTIME" if day % 3 else "PEAK",
            protocol="HTTPS" if day % 2 else "STREAMING",
            app_category="General" if day % 2 else "Video",
            download_gb=(daily_total * Decimal("0.82")).quantize(Decimal("0.001")),
            upload_gb=(daily_total * Decimal("0.18")).quantize(Decimal("0.001")),
            total_gb=daily_total,
            charge=_d("0.00"),
        ))
    if account_index % 6 == 0 and month_index >= 4:
        session.add(ServiceAddon(
            service_account_id=service.id,
            billing_period_id=period.id,
            addon_name="Extra GB 10",
            addon_type="EXTRA_GB",
            valid_from=period.period_start,
            valid_to=period.period_end,
            quantity_gb=_d("10.00"),
            remaining_gb=_d("2.50"),
            charge=_d("350.00"),
        ))


def _seed_invoice_history(session: Session, packages: dict[str, Package], periods: dict[str, BillingPeriod]) -> None:
    package_by_id = {pkg.id: pkg for pkg in packages.values()}
    accounts = session.scalars(select(Account).order_by(Account.id)).all()
    six_periods = [periods[p[0]] for p in _PERIODS_2026]
    for account_index, account in enumerate(accounts, start=1):
        services = session.scalars(
            select(ServiceAccount).where(ServiceAccount.account_id == account.id).order_by(ServiceAccount.id)
        ).all()
        customer = session.get(Customer, account.customer_id)
        for month_index, period in enumerate(six_periods, start=1):
            if _invoice_exists(session, account.id, period.period_start, period.period_end):
                continue
            line_specs: list[tuple[ServiceAccount | None, LineType, str, Decimal, int]] = []
            subtotal = _d("0.00")
            sort_order = 1
            package_names: list[str] = []
            num_services = len(services)
            first_bb_service: ServiceAccount | None = None

            for service in services:
                package = package_by_id.get(service.package_id)
                if package is None:
                    continue
                package_names.append(package.name)
                rental, usage_charge = _service_charge(service, package, month_index, account_index)
                line_specs.append((service, LineType.RENTAL, f"{package.name} [Rental]", rental, sort_order))
                subtotal += rental
                sort_order += 1
                if usage_charge > 0:
                    line_specs.append((service, LineType.USAGE, "Broadband excess usage", usage_charge, sort_order))
                    subtotal += usage_charge
                    sort_order += 1
                _upsert_usage(session, service, package, period, month_index, account_index, usage_charge)

                # Realistic additional charge lines per service type.
                # For 3-service accounts, skip Voice/PeoTV extras to keep rows ≤ ~14.
                if service.service_type == ServiceType.BROADBAND:
                    if first_bb_service is None:
                        first_bb_service = service
                    # Data usage charge — always present (varies by account/month)
                    bb_usage = _d("100.00") + Decimal((month_index + account_index) % 6) * _d("50.00")
                    line_specs.append((service, LineType.USAGE, "Broadband usage charges", bb_usage, sort_order))
                    subtotal += bb_usage
                    sort_order += 1
                    # Static IP fee for ~one-third of accounts (1-2 service accounts only)
                    if num_services <= 2 and account_index % 3 == 1:
                        line_specs.append((service, LineType.FEE, "Static IP address", _d("350.00"), sort_order))
                        subtotal += _d("350.00")
                        sort_order += 1

                elif service.service_type == ServiceType.VOICE and num_services <= 2:
                    call_charge = _d("80.00") + Decimal((month_index + account_index) % 4) * _d("40.00")
                    line_specs.append((service, LineType.USAGE, "Local call charges", call_charge, sort_order))
                    subtotal += call_charge
                    sort_order += 1

                elif service.service_type == ServiceType.PEOTV and num_services <= 2:
                    line_specs.append((service, LineType.FEE, "PeoTV HD decoder rental", _d("150.00"), sort_order))
                    subtotal += _d("150.00")
                    sort_order += 1

            # Discount and addon tied to an actual service so they appear in the PDF group
            discount_service = first_bb_service or (services[0] if services else None)
            if account_index % 5 == 0 and discount_service is not None:
                line_specs.append((discount_service, LineType.DISCOUNT, "Loyalty discount", _d("-250.00"), sort_order))
                subtotal -= _d("250.00")
                sort_order += 1
            addon_total = _d("350.00") if account_index % 6 == 0 and month_index >= 4 else _d("0.00")
            if addon_total and first_bb_service is not None:
                line_specs.append((first_bb_service, LineType.FEE, "Extra GB add-on", addon_total, sort_order))
                subtotal += addon_total

            taxes = (subtotal * Decimal("0.15")).quantize(Decimal("0.01"))
            charges_for_period = (subtotal + taxes).quantize(Decimal("0.01"))
            previous = session.scalar(
                select(Invoice.total_payable)
                .where(Invoice.account_id == account.id, Invoice.period_start < period.period_start)
                .order_by(Invoice.period_start.desc())
                .limit(1)
            ) or _d("0.00")
            payments_received = _d("0.00") if account_index % 8 == 0 else min(Decimal(previous), charges_for_period)
            total_payable = (Decimal(previous) - payments_received + charges_for_period).quantize(Decimal("0.01"))
            invoice = Invoice(
                account_id=account.id,
                invoice_number=f"SIM{account.id:05d}-{period.code.replace('-', '')}",
                billing_date=period.billing_date,
                period_start=period.period_start,
                period_end=period.period_end,
                due_date=period.due_date,
                snapshot_customer_name=customer.full_name if customer else None,
                snapshot_customer_nic=customer.nic if customer else None,
                snapshot_bill_address=_address_text(customer) if customer else None,
                snapshot_account_number=account.account_number,
                snapshot_telephone_number=account.telephone_number,
                snapshot_package_name=", ".join(dict.fromkeys(package_names)) if package_names else None,
                snapshot_service_label=account.service_label,
                balance_bf=previous,
                payments_received=payments_received,
                charges_total=subtotal,
                taxes_total=taxes,
                charges_for_period=charges_for_period,
                total_payable=total_payable,
                status=InvoiceStatus.OVERDUE if account_index % 8 == 0 and month_index == 6 else InvoiceStatus.GENERATED,
            )
            session.add(invoice)
            session.flush()
            for service, line_type, description, amount, line_sort in line_specs:
                session.add(InvoiceLineItem(
                    invoice_id=invoice.id,
                    service_account_id=service.id if service else None,
                    line_type=line_type,
                    description=description,
                    period_start=period.period_start if line_type in {LineType.RENTAL, LineType.USAGE} else None,
                    period_end=period.period_end if line_type in {LineType.RENTAL, LineType.USAGE} else None,
                    amount=amount,
                    sort_order=line_sort,
                ))
            session.add(InvoiceLineItem(
                invoice_id=invoice.id,
                service_account_id=None,
                line_type=LineType.TAX,
                description="Taxes & Levies",
                period_start=None,
                period_end=None,
                amount=taxes,
                sort_order=99,
            ))
            if payments_received > 0:
                session.add(Payment(
                    account_id=account.id,
                    invoice_id=invoice.id,
                    payment_date=period.period_start + timedelta(days=10),
                    method=PaymentMethod.ONLINE,
                    status=PaymentStatus.POSTED,
                    amount=payments_received,
                    reference=f"Online payment {period.code}",
                    receipt_number=f"RCPT-{account.id:05d}-{period.code.replace('-', '')}",
                    provider="SLT Online",
                    provider_reference=f"PG-{account.id:05d}-{period.code.replace('-', '')}",
                    posted_at=datetime.combine(period.period_start + timedelta(days=10), datetime.min.time()),
                ))
        account.last_billed_at = datetime.combine(_PERIODS_2026[-1][3], datetime.min.time())


def _backfill_invoice_snapshots(session: Session) -> None:
    invoices = session.scalars(select(Invoice).where(Invoice.snapshot_customer_name.is_(None))).all()
    for invoice in invoices:
        account = session.get(Account, invoice.account_id)
        customer = session.get(Customer, account.customer_id) if account else None
        services = session.scalars(select(ServiceAccount).where(ServiceAccount.account_id == account.id)).all() if account else []
        package_names: list[str] = []
        for service in services:
            if service.package_id:
                package = session.get(Package, service.package_id)
                if package:
                    package_names.append(package.name)
        invoice.snapshot_customer_name = customer.full_name if customer else None
        invoice.snapshot_customer_nic = customer.nic if customer else None
        invoice.snapshot_bill_address = _address_text(customer) if customer else None
        invoice.snapshot_account_number = account.account_number if account else None
        invoice.snapshot_telephone_number = account.telephone_number if account else None
        invoice.snapshot_package_name = ", ".join(dict.fromkeys(package_names)) if package_names else None
        invoice.snapshot_service_label = account.service_label if account else None


def _seed_realistic_upgrade(session: Session) -> None:
    packages = _package_map(session)
    periods = _period_map(session)
    _enrich_existing_seed_rows(session, packages)
    _create_realistic_customers(session, packages)
    session.flush()
    _seed_invoice_history(session, packages, periods)
    _backfill_invoice_snapshots(session)


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

        try:
            _seed_realistic_upgrade(session)
            session.commit()
            log.info("realistic SLT enrichment complete")
        except Exception:
            session.rollback()
            log.exception("realistic SLT enrichment failed")
            errors += 1

    log.info(
        "done — %d inserted, %d skipped, %d error(s)",
        inserted, skipped, errors,
    )
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
