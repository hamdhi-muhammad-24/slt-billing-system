# BILLING.md — Billing Engine

Spec for the core billing engine (ROADMAP Step 4). The engine turns stored data into a
validated `Bill` object. It is **framework-independent**: no FastAPI, no HTTP, no globals —
just Python + the database via the repository. It must be unit-testable in isolation.

---

## 1. v1 strategy: assemble, don't compute

Line items (rentals, usage, discounts, tax) are **already stored** in `invoice_line_items`
(see DATABASE.md). The engine does NOT compute individual rentals/usage from packages in v1.
It:

1. Fetches the account, its service sub-accounts, the line items, the previous balance, and
   the payments feeding this bill.
2. Sums line items → charges and taxes.
3. Applies the summary formula → totals.
4. Returns a validated `Bill`.

(Computing each line from packages + usage is a LATER enhancement, not Phase 0.)

---

## 2. The math (verified against real bills)

```
charges_total      = sum(item.amount for item if item.line_type != TAX)
taxes_total        = sum(item.amount for item if item.line_type == TAX)
charges_for_period = charges_total + taxes_total

payments_received  = sum(p.amount for p in payments)
arrears            = balance_bf - payments_received        # derived, not stored
total_payable      = arrears + charges_for_period
```

- Discounts are stored as **negative** amounts, so they reduce `charges_total` naturally.
- `balance_bf` for a new invoice = the previous invoice's `total_payable` for that account
  (until real payment reconciliation exists in a later phase).
- Sample-1 check: charges_total 1559.03 + taxes 366.21 = 1925.24; 7703.28 − 5000.00 +
  1925.24 = **4628.52**.

---

## 3. Money rules (critical)

- Use `decimal.Decimal` everywhere. Never `float`.
- Quantize every monetary result to 2 places with `ROUND_HALF_UP`:
  ```python
  TWO_DP = Decimal("0.01")
  def money(x) -> Decimal: return Decimal(x).quantize(TWO_DP, rounding=ROUND_HALF_UP)
  ```
- Sum first, quantize the result (don't quantize each addend mid-sum unless inputs are
  already 2dp, which seed data is).
- DB columns are `NUMERIC(12,2)`; SQLAlchemy returns `Decimal` — keep it that way end to end.

---

## 4. Data model (Pydantic v2) — `app/billing/schemas.py`

The renderer consumes ONLY these objects, never raw rows.

```python
class BillLine(BaseModel):
    service_number: str | None        # None for tax/global lines
    line_type: str                    # RENTAL/USAGE/DISCOUNT/TAX/FEE/ADJUSTMENT
    description: str
    period_start: date | None
    period_end: date | None
    amount: Decimal

class ServiceGroup(BaseModel):        # charges grouped under one sub-account heading
    service_number: str
    service_type: str
    lines: list[BillLine]

class Summary(BaseModel):
    balance_bf: Decimal
    payments_received: Decimal
    arrears: Decimal
    charges_for_period: Decimal
    total_payable: Decimal

class Bill(BaseModel):
    # header
    account_number: str
    telephone_number: str | None
    service_label: str | None
    customer_name: str
    address_lines: list[str]
    invoice_number: str
    billing_date: date
    period_start: date
    period_end: date
    due_date: date
    # body
    groups: list[ServiceGroup]        # charges grouped by sub-account
    tax_lines: list[BillLine]         # Taxes & Levies
    charges_total: Decimal
    taxes_total: Decimal
    summary: Summary
    payments: list[PaymentInfo]       # "Details of Payments Received"
```

Add a validator (or an assert in the engine) that
`summary.total_payable == summary.arrears + summary.charges_for_period` — a self-check that
catches assembly bugs before a PDF is produced.

---

## 5. Repository contract — `app/billing/repository.py`

**The only file containing SQL.** Swapping to SLT's real DB later = rewriting only this file.

```python
def get_bill_inputs(account_number: str, period_start: date, period_end: date) -> BillInputs
# returns a plain container: customer, account, service_accounts, line_items,
# previous_balance (prev invoice total_payable or 0), payments for the period.
```

Rules: parameterised queries only; return typed data (or row objects mapped to dataclasses),
never let the engine import SQLAlchemy models directly.

---

## 6. Engine algorithm — `app/billing/engine.py`

```python
def build_bill(account_number, period_start, period_end) -> Bill:
    inp = repository.get_bill_inputs(account_number, period_start, period_end)

    charges = [l for l in inp.line_items if l.line_type != "TAX"]
    taxes   = [l for l in inp.line_items if l.line_type == "TAX"]

    charges_total = money(sum(l.amount for l in charges))
    taxes_total   = money(sum(l.amount for l in taxes))
    charges_for_period = money(charges_total + taxes_total)

    payments_received = money(sum(p.amount for p in inp.payments))
    arrears       = money(inp.previous_balance - payments_received)
    total_payable = money(arrears + charges_for_period)

    groups = group_lines_by_service(charges, inp.service_accounts)  # preserve sort_order
    return Bill(... assemble header, groups, taxes, summary ...)

def generate_invoice(account_number, period_start, period_end):
    bill = build_bill(...)
    invoice = persist_invoice(bill)      # write invoices + invoice_line_items
    return bill, invoice                 # PDF rendering happens in the cli/renderer step
```

Keep **build** (pure: data → Bill) separate from **persist** and **render**, so the math is
testable without writing a PDF or touching the renderer.

---

## 7. Edge cases to handle (and test in Step 9)

- No payments → `payments_received = 0`, arrears = balance_bf.
- Discount-only sub-account → negative `charges_total` is allowed.
- Zero charges → bill still generates (e.g. only carried arrears).
- Account with one vs. many sub-accounts → grouping works for both.
- Missing previous invoice → `balance_bf = 0`.
- Empty/invalid account → raise a clear error; in batch this becomes a recorded failure, not
  a crash.

---

## 8. Tests — `tests/test_engine.py`

- **Golden test:** the Sample-1 account → `total_payable == Decimal("4628.52")` (and
  charges_for_period == 1925.24, charges_total == 1559.03, taxes_total == 366.21).
- Property: `total_payable == arrears + charges_for_period` for every seeded account.
- One test per edge case in §7.
- All assertions compare `Decimal`, not float.
