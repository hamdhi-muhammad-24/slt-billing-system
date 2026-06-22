# AUTH.md — Phase 3: Auth + Roles

Spec for adding authentication (who you are) and authorization (what you can see)
on top of the frozen backend + frontend. **Docs-first: approve this before building.**

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
- `app/db/models.py` (existing billing models)
- Existing routers' billing logic and SQL
- Frontend pages + the one-HTTP-client rule (`src/lib/api.ts`)

## New — additive only

- `app/auth/` module (config additions, hashing, JWT, dependencies)
- `app/auth/models.py` — the **users** table (separate from billing models)
- `app/auth/repository.py` — auth's own SQL (billing repository stays untouched)
- A **new** Alembic migration for the users table
- `/auth` router
- `Depends(...)` guards applied to existing routers — **sanctioned additive change**
  (same exception class as CORS; routers gain a guard, their logic is not rewritten)
- Frontend: real JWT replaces the mock-auth shell (auth layer + api client only)

---

## Data model — `users`

| Column         | Type                    | Notes                                  |
|----------------|-------------------------|----------------------------------------|
| id             | PK                      |                                        |
| email          | text, unique, not null  | login identifier                       |
| password_hash  | text, not null          | bcrypt; never plaintext                |
| role           | enum `ADMIN`/`CUSTOMER` |                                        |
| customer_id    | FK → customers.id, NULL | NULL for admins; set for customers     |
| is_active      | bool, default true      | inactive → cannot log in               |
| created_at     | timestamptz             |                                        |

New migration only. Existing tables/enums are not modified.

---

## Password hashing

- `passlib` with **bcrypt**.
- Store only the hash. Never store, return, or log a plaintext password.

---

## JWT

- FastAPI OAuth2 password flow (`OAuth2PasswordBearer`).
- Algorithm HS256; secret from `.env` (documented in `.env.example`, real `.env` gitignored).
- Access token only in v1 (no refresh token — note for later).
- Expiry configurable, default **60 min**.
- Claims: `sub` (user id), `role`, `customer_id`, `exp`.

---

## Endpoints — `/auth`

| Method | Path         | Body                          | Returns                          |
|--------|--------------|-------------------------------|----------------------------------|
| POST   | `/auth/login`| form: `username`(=email),`password` | `{ access_token, token_type }` |
| GET    | `/auth/me`   | — (Bearer token)              | current user: id, email, role, customer_id |

---

## Authorization rules

Dependencies in `app/auth/dependencies.py`:

- `get_current_user` — decode token, load user, **401** if invalid / expired / inactive.
- `require_admin` — **403** if role is not ADMIN.
- `scope_to_customer` — for CUSTOMER, restrict queries to their `customer_id`.

Applied:

- **ADMIN-only:** billing generate-one / generate-batch, run status, full customer list.
- **CUSTOMER-scoped:** `/customers/me`-style reads, `/accounts/{id}`, `/accounts/{id}/invoices`,
  PDF download — all filtered to their own `customer_id`.
- Accessing another customer's resource → **404** (don't leak existence). Decide & keep consistent.

Routers receive a guard via `Depends`; their internal logic is unchanged.

---

## PDF access — short-lived signed links

No S3 yet (that's Phase 6), so no real presigned URLs. v1 keeps the same security property:

- API issues a **signed, expiring token** for a specific invoice's PDF
  (`itsdangerous` or a short-exp JWT; payload `{ invoice_id, exp ~5 min }`).
- The PDF endpoint accepts **either** a valid logged-in authorized user **or** a valid signed token.
- Swappable to real S3 presigned URLs in Phase 6 by changing only this one layer.

---

## Security / PII

- JWT secret + token expiry + bcrypt cost live in `.env`; `.env.example` documents them.
- No passwords, tokens, or PII in logs.
- All users synthetic.

---

## Seed users (so you can actually log in)

- 1 admin: `admin@slt.lk`
- A few customers, each mapped to an existing seeded customer (`customer_id` set).
- Dev passwords are synthetic and documented in seed output / `.env.example`.
- Seeding is idempotent (safe to re-run).

---

## Frontend changes (Phase 2 shell → real JWT)

- Replace mock login with `POST /auth/login`; store `access_token`.
- `src/lib/api.ts`: attach `Authorization: Bearer <token>` to every request (one place).
- Route guards read role from `/auth/me` (or decoded token).
- Logout clears the token; 401 from API forces re-login.
- Token stays in `localStorage` for now (harden later).
- `formatLKR` and money-as-string rules unchanged.

---

## Final acceptance (end of phase — one full test)

1. Admin logs in → sees all customers, can trigger billing.
2. Customer logs in → sees only own accounts/invoices, downloads own PDF.
3. Customer cannot reach another customer's invoice (consistent 404).
4. Expired / invalid token → 401.
5. Account 1 `total_payable` still **4628.52** end-to-end through the UI.
6. `pytest -q` green, including new auth + scoping tests.

---

## Build chunks (3 — one smoke-check each, commit after each)

- **A — Backend auth foundation:** users model + migration, `app/auth/` (hashing, JWT,
  dependencies), `/auth/login` + `/auth/me`, seed users.
  ✅ check: log in via `/auth/login`, receive a token; `/auth/me` returns the user.

- **B — Authorization + scoping + signed PDF links:** apply guards to existing routers,
  scope CUSTOMER reads, signed short-lived PDF links.
  ✅ check: admin lists all customers (200); customer hitting another customer's account → 404.

- **C — Frontend JWT swap:** real login, Bearer token in api client, role-based guards, logout.
  ✅ check: full login as both roles; account 1 shows 4628.52.
