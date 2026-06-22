# AUTH.md — Phase 3: Auth + Roles

Spec for adding authentication (who you are) and authorization (what you can see)
on top of the frozen backend + frontend. **Docs-first.**

> **Schema note (corrected to match reality):** the `users` table, `user_role` enum,
> and the user<->customer link **already exist** in frozen Phase 0 `app/db/models.py`
> and the initial migration. The link is **`customers.user_id -> users.id`** (NOT
> `users.customer_id`). Phase 3 adds **no migration** and edits **no frozen file**.

---

## Goal

- Log in with email + password, get a JWT.
- Two roles: **ADMIN** and **CUSTOMER**.
- ADMIN sees everything and can trigger billing.
- CUSTOMER sees **only their own** customer's accounts, invoices, and PDFs.
- PDFs are served via short-lived signed links, not public URLs.
- No PII or secrets in logs or git.

---

## Frozen — do NOT edit

- `app/billing/` (engine, schemas, repository)
- `app/pdf/`
- `app/db/models.py` (users + customers already live here, frozen)
- The initial Alembic migration
- Existing routers' billing logic and SQL
- Frontend pages + the one-HTTP-client rule (`src/lib/api.ts`)

## New — additive only

- `app/auth/` module: `security.py`, `repository.py`, `schemas.py`,
  `dependencies.py`, `router.py`, `seed.py`
  (`app/auth/models.py` only re-exports `User`/`UserRole` from frozen models)
- `/auth` router, wired with `include_router`
- `Depends(...)` guards on existing routers — **sanctioned additive change**
  (like CORS; guards raise before the body runs, the body is not rewritten)
- Frontend: real JWT replaces the mock-auth shell (auth layer + api client only)
- **No new migration.**

---

## Data model — `users` (already exists, frozen)

| Column         | Type                         |
|----------------|------------------------------|
| id             | PK                           |
| email          | text, unique, not null       |
| password_hash  | text, not null (bcrypt)      |
| role           | enum `user_role` ADMIN/CUSTOMER |
| is_active      | bool, default true           |
| created_at     | timestamptz                  |

Link: **`customers.user_id -> users.id`** (nullable). To find a user's customer,
query the `Customer` whose `user_id == current_user.id`. Kept one-to-one by
application + seed logic.

---

## Password hashing

- `passlib` with **bcrypt**. Store only the hash. Never store/return/log plaintext.

---

## JWT

- FastAPI OAuth2 password flow (`OAuth2PasswordBearer`), HS256.
- Secret + expiry from `.env` (documented in `.env.example`, real `.env` gitignored).
- Access token only in v1 (no refresh — note for later). Default expiry 60 min.
- Claims: `sub` (user id), `role`, `exp`. Customer id is resolved server-side
  from `customers.user_id`, not stored in the token.

---

## Endpoints — `/auth`

| Method | Path          | Body                                 | Returns                              |
|--------|---------------|--------------------------------------|--------------------------------------|
| POST   | `/auth/login` | form: `username`(=email), `password` | `{ access_token, token_type }`       |
| GET    | `/auth/me`    | Bearer token                         | id, email, role, customer_id-or-null |

---

## Authorization rules

Dependencies in `app/auth/dependencies.py`:

- `get_current_user` — decode token, load user, **401** if invalid/expired/inactive.
- `require_admin` — **403** if role is not ADMIN.
- Ownership guard — for a CUSTOMER hitting a resource scoped by account/invoice,
  resolve the owning customer and compare to the current user's customer
  (`customers.user_id == current_user.id`). Mismatch → **404** (don't leak existence).
  ADMIN bypasses.

Applied:

- **ADMIN-only:** billing generate-one / generate-batch, run status, full customer list.
- **CUSTOMER-scoped:** their own accounts, invoices, and PDF download via the
  ownership guard (admin bypasses).

Guards are added via `Depends`; router bodies are not rewritten. If "list only my
own" needs a new shape, add a **new** scoped endpoint rather than editing a frozen one.

---

## PDF access — short-lived signed links

No S3 yet (Phase 6). Same security property now:

- API issues a **signed, expiring token** for a specific invoice's PDF
  (`itsdangerous` or short-exp JWT; payload `{ invoice_id, exp ~5 min }`).
- The PDF endpoint accepts a valid logged-in **authorized** user **or** a valid signed token.
- Swappable to real S3 presigned URLs in Phase 6 — only this layer changes.

---

## Security / PII

- JWT secret + expiry + bcrypt cost in `.env`; `.env.example` documents them.
- No passwords/tokens/PII in logs. All users synthetic.

---

## Seed users

- 1 admin: `admin@slt.lk`.
- A few CUSTOMER users, each linked by setting `customers.user_id` on an existing
  seeded customer.
- Synthetic dev passwords printed by the seed script. Idempotent.

---

## Final acceptance (end of phase — one full test)

1. Admin logs in → sees all customers, can trigger billing.
2. Customer logs in → sees only own accounts/invoices, downloads own PDF.
3. Customer cannot reach another customer's invoice (consistent 404).
4. Expired/invalid token → 401.
5. Account 1 `total_payable` still **4628.52** end-to-end through the UI.
6. `pytest -q` green, including auth + scoping tests.

---

## Build chunks (3 — one smoke-check each, commit after each)

- **A — Backend auth foundation (DONE):** `app/auth/` security, repository, schemas,
  dependencies, router, seed users. No migration (schema already existed).
  ✅ log in via `/auth/login`, token works, `/auth/me` returns the user.

- **B — Authorization + scoping + signed PDF links:** guards on existing routers,
  CUSTOMER ownership scoping, signed short-lived PDF links.
  ✅ admin lists all customers (200); customer hitting another customer's account → 404.

- **C — Frontend JWT swap:** real login, Bearer token in api client, role-based guards, logout.
  ✅ full login as both roles; account 1 shows 4628.52.
