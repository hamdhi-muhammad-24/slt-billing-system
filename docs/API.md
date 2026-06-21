# API.md — Phase 1: FastAPI Backend

> REST API layered **over** the existing billing engine, repository, and PDF generator.
> The engine, repository, and PDF code from Phase 0 are **not modified**. The API only calls them.

---

## 1. Goal & principles

- Expose Phase 0 capabilities (read billing data, generate invoices, download PDFs) over HTTP.
- **Thin API layer.** Routers validate input and shape output; they contain no billing math.
- **Engine untouched.** Billing logic stays testable without the API.
- **One repository.** All DB access still lives in the single repository file. Routers never write SQL.
- **Money is exact.** `Decimal` everywhere internally; serialized as a **string** in JSON (e.g. `"4628.52"`), never a float.
- **Invoices are frozen snapshots.** The API reads stored invoice totals; it never recomputes a stored invoice.
- **No auth yet.** Auth + roles arrive in Phase 3. Phase 1 endpoints are open (local/dev only).

---

## 2. Layering

```
HTTP request
   │
   ▼
app/api/routers/*      ← FastAPI routers (thin: validate, call, shape)
   │
   ▼
app/api/schemas.py     ← Pydantic request/response models
   │
   ▼
app/billing/  (engine)   app/db/repository.py   app/pdf/  (generator)
   └── UNTOUCHED Phase 0 code ──────────────────────────────┘
```

Routers depend **inward** only. The engine/repository/PDF never import from `app/api/`.

---

## 3. Tech decisions

| Concern        | Choice                                  |
|----------------|-----------------------------------------|
| Framework      | FastAPI                                 |
| Models         | Pydantic v2                             |
| Server         | uvicorn (dev: `--reload`)               |
| DB session     | Reuse Phase 0 SQLAlchemy session/engine |
| Money in JSON  | `Decimal` → string via serializer       |
| Pagination     | `limit` + `offset`, envelope response   |
| Errors         | JSON `{ "detail": ... }`                |

---

## 4. Money serialization

Internally all amounts stay `Decimal`. In API responses they serialize to a 2-dp string.

```python
from decimal import Decimal
from typing import Annotated
from pydantic import PlainSerializer

Money = Annotated[
    Decimal,
    PlainSerializer(lambda v: f"{v:.2f}", return_type=str),
]
```

Use `Money` for every monetary field in response schemas. JSON shows `"4628.52"`, not `4628.52`.

---

## 5. New files (added in Phase 1)

```
app/api/
  __init__.py
  main.py            # app factory: create_app(), mounts routers, exception handlers
  deps.py            # dependencies: get_db session, get_repository
  schemas.py         # all Pydantic request/response models
  errors.py          # error response model + exception handlers
  routers/
    __init__.py
    health.py
    customers.py
    accounts.py
    invoices.py
    billing.py
tests/api/
  test_health.py
  test_reads.py
  test_billing.py    # includes the 4628.52 correctness test through HTTP
```

Run target: `py -3.11 -m uvicorn app.api.main:app --reload`

---

## 6. Pagination envelope

List endpoints accept `?limit=` (default 50, max 200) and `?offset=` (default 0) and return:

```json
{
  "items": [ ... ],
  "total": 8,
  "limit": 50,
  "offset": 0
}
```

---

## 7. Schemas (response shapes)

Field names mirror the DB columns. Amounts use `Money` (string in JSON).

**CustomerOut** — `id, name, nic, email, phone, address`
**AccountOut** — `id, customer_id, account_no, status, billing_cycle`
**ServiceAccountOut** — `id, account_id, service_type (voice|broadband|peotv), identifier, package_id`
**PackageOut** — `id, name, service_type, monthly_rental (Money)`
**InvoiceLineItemOut** — `id, service_account_id, description, amount (Money), is_tax, sort_order`
  - discounts are **negative** `amount`; taxes have `is_tax = true`
**InvoiceOut** (frozen snapshot) —
  `id, account_id, period, issue_date, due_date,`
  `balance_bf (Money), payments_received (Money), arrears (Money),`
  `charges_for_period (Money), total_payable (Money),`
  `service_accounts: [ServiceAccountSummary], line_items: [InvoiceLineItemOut]`
**PaymentOut** — `id, account_id, amount (Money), paid_at, method, reference`
**BillingRunOut** — `id, period, status (pending|running|done|failed), total, succeeded, failed, started_at, finished_at`
**BillingRunFailureOut** — `id, run_id, account_id, error`

> Invariant the API surfaces but never recomputes for stored invoices:
> `total_payable = (balance_bf − payments_received) + charges_for_period`
> where `arrears = balance_bf − payments_received`, and `charges_for_period` already includes taxes and negative discounts.

---

## 8. Request bodies

**GenerateOneRequest** — `{ account_id: int, period: "YYYY-MM" }`
**GenerateBatchRequest** — `{ period: "YYYY-MM", account_ids?: int[] }`  *(omit `account_ids` = all active accounts)*

---

## 9. Endpoints

| Method | Path                                   | Purpose                                   |
|--------|----------------------------------------|-------------------------------------------|
| GET    | `/health`                              | Liveness + DB reachable                   |
| GET    | `/customers`                           | List customers (paginated)                |
| GET    | `/customers/{customer_id}`             | One customer                              |
| GET    | `/customers/{customer_id}/accounts`    | Accounts for a customer                   |
| GET    | `/accounts/{account_id}`               | One account                               |
| GET    | `/accounts/{account_id}/service-accounts` | Sub-accounts (voice/broadband/peotv)   |
| GET    | `/accounts/{account_id}/invoices`      | Invoices for an account (paginated)       |
| GET    | `/accounts/{account_id}/payments`      | Payments for an account                   |
| GET    | `/invoices/{invoice_id}`               | One invoice (frozen snapshot + line items)|
| GET    | `/invoices/{invoice_id}/pdf`           | Download the rendered PDF                 |
| POST   | `/billing/generate-one`                | Generate one invoice → returns InvoiceOut |
| POST   | `/billing/generate-batch`              | Start a batch run → returns BillingRunOut |
| GET    | `/billing/runs/{run_id}`               | Batch run status + failures               |

### Endpoint notes

- **`GET /invoices/{id}/pdf`** → `200` with `Content-Type: application/pdf`, header
  `Content-Disposition: attachment; filename="invoice-{id}.pdf"`. Reuses the Phase 0 PDF generator. Stream bytes; do not write to disk per request.
- **`POST /billing/generate-one`** → `201` with `InvoiceOut`. If an invoice already exists for that `account_id`+`period`, return `409` (do not duplicate a frozen snapshot).
- **`POST /billing/generate-batch`** → `202` with `BillingRunOut`. Phase 1 may run synchronously (loop accounts, record per-account failures in `billing_run_failures`). True async scheduling is Phase 4 — keep the response shape compatible so nothing changes later.

---

## 10. Status codes & errors

| Code | When                                              |
|------|---------------------------------------------------|
| 200  | Read OK                                            |
| 201  | Invoice created (`generate-one`)                  |
| 202  | Batch run accepted (`generate-batch`)             |
| 404  | Unknown id (customer/account/invoice/run)         |
| 409  | Invoice already exists for account+period         |
| 422  | Validation error (FastAPI default)                |
| 500  | Unexpected (logged; generic `detail`)             |

Error body: `{ "detail": "Invoice 999 not found" }`. Map a `NotFound` domain error → 404, a `DuplicateInvoice` → 409 via exception handlers in `errors.py`.

---

## 11. Out of scope (later phases)

- Auth / JWT / roles → **Phase 3** (then `/customers/me/...`, ownership checks).
- Async/scheduled billing → **Phase 4** (Celery/APScheduler); batch endpoint shape stays the same.
- Notifications → **Phase 5**. Docker/AWS → **Phase 6**.

---

## 12. Acceptance check (Definition of Done)

1. `py -3.11 -m uvicorn app.api.main:app --reload` starts; `/docs` (Swagger) loads.
2. `GET /health` → `200`, DB reachable.
3. `GET /accounts/{sample}/invoices` and `GET /invoices/{id}` return correct data; **money fields are strings**.
4. `POST /billing/generate-one` for the sample account returns `total_payable = "4628.52"`.
5. `GET /invoices/{id}/pdf` downloads a valid PDF identical to the Phase 0 CLI output.
6. `pytest tests/api` passes, including the 4628.52 test through HTTP.
