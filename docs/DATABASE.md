# DATABASE.md — SLT E-Bill Schema

Production PostgreSQL schema, derived from the real SLT sample bills. This is **our** schema.
When SLT's real DB arrives, only `app/billing/repository.py` changes (see CLAUDE.md §swap).

---

## 1. Rules

- Money = `NUMERIC(12,2)` → Python `Decimal`. Never `float`.
- An invoice is a **frozen snapshot**: summary totals are stored, not recomputed. Past bills
  never change.
- One account → **many service sub-accounts** (voice / broadband / PeoTV). Charges group under them.
- Line items are **signed**: discounts are negative, so summing is one operation.
- Enums = native PG types. Timestamps = `TIMESTAMPTZ DEFAULT now()`.
- IDs = `BIGINT GENERATED ALWAYS AS IDENTITY`.

---

## 2. Entity Map

```
users ─< customers ─< accounts ─< service_accounts ─< invoice_line_items
                          │              └─< usage_records       ▲
                          ├─< invoices ──────────────────────────┘
                          └─< payments
packages (catalogue, used by later real computation)
billing_runs ─< billing_run_failures
```

---

## 3. Enums

```sql
CREATE TYPE user_role      AS ENUM ('ADMIN','CUSTOMER');
CREATE TYPE account_status AS ENUM ('ACTIVE','SUSPENDED','CLOSED');
CREATE TYPE service_type   AS ENUM ('VOICE','BROADBAND','PEOTV','BUNDLE','OTHER');
CREATE TYPE line_type      AS ENUM ('RENTAL','USAGE','DISCOUNT','TAX','FEE','ADJUSTMENT');
CREATE TYPE invoice_status AS ENUM ('DRAFT','GENERATED','SENT','PAID','OVERDUE','CANCELLED');
CREATE TYPE payment_method AS ENUM ('PHYSICAL','ONLINE','CARD','CHEQUE','BANK_TRANSFER');
CREATE TYPE run_status     AS ENUM ('PENDING','RUNNING','DONE','PARTIAL','FAILED');
```

---

## 4. Tables (DDL)

```sql
-- login layer (used in later auth phase)
CREATE TABLE users (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          user_role NOT NULL DEFAULT 'CUSTOMER',
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE customers (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id       BIGINT REFERENCES users(id) ON DELETE SET NULL,
    full_name     TEXT NOT NULL,
    address_line1 TEXT,
    address_line2 TEXT,
    city          TEXT,
    postal_code   TEXT,
    status        account_status NOT NULL DEFAULT 'ACTIVE',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- main billing account (bill header)
CREATE TABLE accounts (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id      BIGINT NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    account_number   TEXT NOT NULL UNIQUE,     -- "004 152 4075"
    telephone_number TEXT,                      -- "0359236535"
    service_label    TEXT,                      -- "HOME" / "LTE service"
    status           account_status NOT NULL DEFAULT 'ACTIVE',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_accounts_customer ON accounts(customer_id);

-- sub-accounts that group charges on the bill
CREATE TABLE service_accounts (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_id     BIGINT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    service_number TEXT NOT NULL,               -- "0359236535","940359236535","AD2235051"
    service_type   service_type NOT NULL,
    label          TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_service_accounts_account ON service_accounts(account_id);

-- plan catalogue (later real computation)
CREATE TABLE packages (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name                TEXT NOT NULL,
    service_type        service_type NOT NULL,
    monthly_fee         NUMERIC(12,2) NOT NULL DEFAULT 0,
    data_limit_gb       NUMERIC(10,2),
    extra_charge_per_gb NUMERIC(12,2) DEFAULT 0,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE
);

-- usage detail (voice usage, per-channel TV in the PNG sample)
CREATE TABLE usage_records (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_account_id BIGINT NOT NULL REFERENCES service_accounts(id) ON DELETE CASCADE,
    period_start       DATE NOT NULL,
    period_end         DATE NOT NULL,
    metric             TEXT,            -- "data_gb","voice_minutes","channel"
    description        TEXT,            -- "ANIMAL PLANET"
    quantity           NUMERIC(12,3),
    charge             NUMERIC(12,2) DEFAULT 0,
    event_time         TIMESTAMPTZ
);
CREATE INDEX idx_usage_service ON usage_records(service_account_id);

-- one per account per period (snapshot)
CREATE TABLE invoices (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_id         BIGINT NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT,
    invoice_number     TEXT NOT NULL UNIQUE,    -- "0038474527-0337"
    billing_date       DATE NOT NULL,
    period_start       DATE NOT NULL,
    period_end         DATE NOT NULL,
    due_date           DATE NOT NULL,
    balance_bf         NUMERIC(12,2) NOT NULL DEFAULT 0,
    payments_received  NUMERIC(12,2) NOT NULL DEFAULT 0,
    charges_total      NUMERIC(12,2) NOT NULL DEFAULT 0,   -- non-tax items
    taxes_total        NUMERIC(12,2) NOT NULL DEFAULT 0,
    charges_for_period NUMERIC(12,2) NOT NULL DEFAULT 0,   -- charges_total + taxes_total
    total_payable      NUMERIC(12,2) NOT NULL DEFAULT 0,
    status             invoice_status NOT NULL DEFAULT 'GENERATED',
    pdf_path           TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (account_id, period_start, period_end)         -- idempotent runs
);
CREATE INDEX idx_invoices_account ON invoices(account_id);
CREATE INDEX idx_invoices_period  ON invoices(period_start, period_end);

-- every charge row (arrears = balance_bf - payments_received is derived, not stored)
CREATE TABLE invoice_line_items (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    invoice_id         BIGINT NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    service_account_id BIGINT REFERENCES service_accounts(id) ON DELETE SET NULL, -- NULL = tax
    line_type          line_type NOT NULL,
    description        TEXT NOT NULL,
    period_start       DATE,                    -- split-period rentals
    period_end         DATE,
    amount             NUMERIC(12,2) NOT NULL,  -- signed; discounts negative
    sort_order         INT NOT NULL DEFAULT 0
);
CREATE INDEX idx_line_items_invoice ON invoice_line_items(invoice_id);

CREATE TABLE payments (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_id   BIGINT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    payment_date DATE NOT NULL,
    method       payment_method NOT NULL DEFAULT 'PHYSICAL',
    amount       NUMERIC(12,2) NOT NULL,
    reference    TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_payments_account ON payments(account_id);

CREATE TABLE billing_runs (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    period_start   DATE NOT NULL,
    period_end     DATE NOT NULL,
    status         run_status NOT NULL DEFAULT 'PENDING',
    total_accounts INT NOT NULL DEFAULT 0,
    succeeded      INT NOT NULL DEFAULT 0,
    failed         INT NOT NULL DEFAULT 0,
    started_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at    TIMESTAMPTZ
);

CREATE TABLE billing_run_failures (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    billing_run_id BIGINT NOT NULL REFERENCES billing_runs(id) ON DELETE CASCADE,
    account_id     BIGINT REFERENCES accounts(id) ON DELETE SET NULL,
    error_message  TEXT NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## 5. Bill Region → Table

| Bill region | Table(s) |
|---|---|
| Telephone / Account no / service label | `accounts` |
| Customer name + address | `customers` |
| Invoice no, dates, due date | `invoices` |
| Summary boxes (B/F, Payments, Charges, Total) | `invoices` (snapshot) |
| Charge lines grouped by sub-account | `service_accounts` + `invoice_line_items` |
| Discounts (negative) | `invoice_line_items` (DISCOUNT) |
| Taxes & Levies | `invoice_line_items` (TAX) |
| Payments Received detail | `payments` |
| Per-channel / usage detail | `usage_records` |

---

## 6. Engine Formulas

```
charges_total      = SUM(amount) WHERE line_type <> 'TAX'
taxes_total        = SUM(amount) WHERE line_type =  'TAX'
charges_for_period = charges_total + taxes_total
arrears            = balance_bf - payments_received          (derived, not stored)
total_payable      = arrears + charges_for_period
```
New invoice `balance_bf` = previous invoice `total_payable` for that account (until real
payment reconciliation exists). All math in `Decimal`, 2 dp, `ROUND_HALF_UP`.

---

## 7. Seed Example (Sample 1 — verified to the cent)

```sql
INSERT INTO customers (full_name, address_line1, city, postal_code)
VALUES ('Pavithim Nayapila Senadira','No 807/102 Welimada Road','Badulla','90200');

INSERT INTO accounts (customer_id, account_number, telephone_number, service_label)
VALUES (1,'004 152 4075','0359236535','LTE service');

INSERT INTO service_accounts (account_id, service_number, service_type, label) VALUES
 (1,'0359236535','VOICE','SLT Voice Service 4G Net pal'),
 (1,'940359236535','BROADBAND','SLT BroadBand Service LTE Web Family Plus');

INSERT INTO payments (account_id, payment_date, method, amount, reference)
VALUES (1,'2024-02-16','PHYSICAL',5000.00,'Physical payment');

-- 7703.28 - 5000.00 + 1925.24 = 4628.52
INSERT INTO invoices (account_id, invoice_number, billing_date, period_start, period_end,
  due_date, balance_bf, payments_received, charges_total, taxes_total,
  charges_for_period, total_payable, status)
VALUES (1,'0038474527-0337','2024-02-25','2024-01-24','2024-02-23','2024-03-17',
  7703.28,5000.00,1559.03,366.21,1925.24,4628.52,'GENERATED');

INSERT INTO invoice_line_items (invoice_id, service_account_id, line_type, description,
  period_start, period_end, amount, sort_order) VALUES
 (1,1,'RENTAL','SLT Voice Service 4G Net pal [Rental]','2024-01-24','2024-02-16',   0.00,1),
 (1,1,'RENTAL','SLT Voice Service 4G Net pal [Rental]','2024-02-17','2024-02-23',   0.00,2),
 (1,2,'RENTAL','SLT BroadBand Service LTE Web Family Plus [Rental]','2024-01-24','2024-02-12',1154.84,3),
 (1,2,'RENTAL','SLT BroadBand Service LTE Web Family Plus [Rental]','2024-02-17','2024-02-23', 404.19,4),
 (1,NULL,'TAX','Taxes & Levies',NULL,NULL,366.21,99);
```

**Check:** 1154.84 + 404.19 = 1559.03; + 366.21 = 1925.24; 7703.28 − 5000.00 + 1925.24 = **4628.52** ✓

Seed 5–10 accounts of varied shape: single sub-account, three sub-accounts, one with a
discount line, one with zero balance, one with carried arrears. This exercises every path.
