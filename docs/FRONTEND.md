# FRONTEND.md — Phase 2: React Portals

> Two browser portals (**Admin** + **Customer**) built **over** the Phase 1 FastAPI backend.
> The frontend only calls the HTTP API. It never touches the database, the billing engine, or the PDF generator directly.

---

## 1. Goal & principles

- Expose Phase 1 endpoints through two UIs: an **Admin portal** (staff) and a **Customer portal** (end users).
- **Thin client.** Components render data and call the API; no billing math in the browser.
- **Backend stays frozen (almost).** One small *additive* change: enable CORS in the API layer so the browser can call it. Engine / repository / PDF are untouched.
- **Money is exact, never float.** Amounts arrive as strings (`"4628.52"`) and are displayed as strings. The frontend never runs `Number()` / `parseFloat()` on money.
- **Invoices are frozen snapshots.** The UI shows stored invoice totals as-is; it never recomputes.
- **Auth is a thin, swappable shell.** Phase 2 ships a mock session (login + route guard). A later phase swaps only the auth layer for real JWT — the frontend analogue of your swappable repository.
- **One HTTP client.** All network calls live in one typed module — the frontend mirror of "all DB access in one repository file."

---

## 2. Layering

```
Browser (React)
  pages / components      ← render + handle events (no business logic)
      │
      ▼
  hooks (TanStack Query)  ← fetch + cache, loading & error states
      │
      ▼
  lib/api.ts              ← single typed HTTP client (base URL, future auth header)
      │
      ▼  HTTP (JSON / PDF bytes)
  FastAPI backend (Phase 1)  ── UNTOUCHED except CORS ──
```

Dependencies point downward only. Pages never call `fetch` directly — they go through hooks → client.

---

## 3. Tech decisions

| Concern        | Choice                                      |
|----------------|---------------------------------------------|
| Build tool     | Vite                                        |
| Language       | TypeScript                                  |
| UI library     | React                                       |
| Styling        | Tailwind CSS                                |
| Components     | shadcn/ui                                   |
| Routing        | React Router                                |
| Data fetching  | TanStack Query (React Query)                |
| HTTP           | `fetch` wrapper in `lib/api.ts`             |
| Money          | string end-to-end; display only, never float|
| Auth (Phase 2) | mock session in one `AuthProvider`          |
| API base URL   | `VITE_API_BASE_URL` env var                 |

---

## 4. Where it lives

```
repo-root/
  app/            # Phase 0–1 backend (frozen except CORS)
  docs/
  frontend/       # ← Phase 2 lives entirely here
    src/
      lib/api.ts          # single HTTP client
      lib/money.ts        # display helpers (no math)
      auth/AuthProvider.tsx
      auth/RequireRole.tsx
      hooks/              # one hook per resource (TanStack Query)
      components/
      pages/admin/
      pages/customer/
      types.ts            # mirrors API.md §7
      App.tsx
      main.tsx
    .env                  # VITE_API_BASE_URL=http://localhost:8000
    package.json
```

`frontend/` is self-contained. Backend never imports from it, and it never imports backend code.

---

## 5. Money on the frontend

Amounts arrive as 2-dp strings. Rule: **display, don't compute.**

```ts
// lib/money.ts
export const formatLKR = (v: string) => `Rs. ${v}`; // v is already "4628.52"
```

Never `Number(v)` / `parseFloat(v)` for display. If a future feature needs arithmetic it uses a decimal-safe library — but Phase 2 only displays.

---

## 6. Types (mirror the API)

`src/types.ts` mirrors API.md §7 response shapes. Every money field is typed `string`:

- `Customer`, `Account`, `ServiceAccount`, `Package`
- `Invoice` (with `line_items`, `service_accounts`), `InvoiceLineItem`
- `Payment`, `BillingRun`, `BillingRunFailure`
- `Paginated<T> = { items: T[]; total: number; limit: number; offset: number }`

---

## 7. HTTP client (one module)

`src/lib/api.ts` — one wrapper around `fetch`:

- reads base URL from `import.meta.env.VITE_API_BASE_URL`
- sets JSON headers; (later) attaches the auth token in **one** place
- on non-2xx, throws a typed `ApiError { status, detail }` mapped from the backend `{ "detail": ... }`
- `downloadInvoicePdf(id)` → fetch blob → trigger a browser download

Components never call `fetch`; they use hooks that call this client.

---

## 8. Auth shell (mock — Phase 2)

- `AuthProvider` holds `{ role: 'admin' | 'customer', customerId? }` in React state (+ optional `localStorage` to survive refresh).
- **Login page** = dev shim: choose **Admin**, or choose **Customer** + pick which customer id to act as. Clearly labelled "dev login".
- `RequireRole` guards routes; no session → redirect to `/login`.
- Logout clears the session.
- **Swap point:** later, replace the login action with `POST /auth/login` → JWT and attach the token in `lib/api.ts`. Nothing else changes.

---

## 9. Routes & pages

**Shared:** `/login`

**Admin** (`/admin/*`, role = admin):
- `/admin` — Dashboard: counts (customers / accounts / invoices) + recent billing runs
- `/admin/customers` → `/admin/customers/:id` (customer + their accounts)
- `/admin/accounts/:id` — service accounts, invoices, payments
- `/admin/invoices/:id` — frozen snapshot + line items + **Download PDF**
- `/admin/billing` — Generate one, Generate batch, view run status

**Customer** (`/app/*`, role = customer, scoped to `customerId`):
- `/app` — My accounts
- `/app/accounts/:id` — my invoices
- `/app/invoices/:id` — snapshot + **Download PDF**

Customer pages only ever request data for the logged-in `customerId`. (Real server-side ownership checks come with the auth phase; Phase 2 enforces in-client only.)

---

## 10. Endpoints used (all from Phase 1)

Read: `/customers`, `/customers/:id`, `/customers/:id/accounts`, `/accounts/:id`, `/accounts/:id/service-accounts`, `/accounts/:id/invoices`, `/accounts/:id/payments`, `/invoices/:id`, `/invoices/:id/pdf`.

Write: `POST /billing/generate-one`, `POST /billing/generate-batch`, `GET /billing/runs/:id`.

**No new backend endpoints are required.** If the dashboard needs counts, derive them from `total` in the list envelopes — do not add backend endpoints in this phase.

---

## 11. Backend prerequisite (one additive change)

The browser calls the API from a different origin (`http://localhost:5173`). Enable CORS **in the API layer only**:

- add `CORSMiddleware` (allowing the dev origin) in `app/api/main.py`.

This is additive and lives in the API layer — engine / repository / PDF stay frozen.

---

## 12. UX baseline

Every data view handles three states: **loading**, **error** (show the `detail` message), **empty**. Lists are tables; the invoice detail is a clean "snapshot" card. UI text is English in Phase 2 (Sinhala/Tamil remain PDF-only).

---

## 13. Out of scope (later phases)

- Real auth / JWT / server-side ownership → auth phase.
- Creating payments, editing customers, live async billing progress.
- UI internationalisation, theme polish, deployment/hosting.

---

## 14. Acceptance check (Definition of Done)

1. `npm run dev` serves the app; `/login` loads.
2. CORS works: the admin dashboard loads live data with no CORS error.
3. Admin → customer 1 → account 1 → its invoice shows `total_payable` exactly **`"4628.52"`** (string, not float).
4. **Download PDF** on that invoice returns the same PDF as the Phase 0/1 output.
5. Admin can Generate one / Generate batch and see run status; a duplicate shows the 409 message cleanly.
6. Customer login is scoped: a customer sees only their own accounts/invoices.
7. No money value is ever rendered via float / `parseFloat`.
8. `npm run build` succeeds with no type errors.

---

## 15. Build order (each step = one verified commit)

0. Write this doc + add it to the `CLAUDE.md` index — commit.
1. Enable CORS in `app/api/main.py`; verify from the browser — commit.
2. Scaffold Vite + TS + Tailwind + shadcn in `frontend/`; app runs — commit.
3. `types.ts` + `lib/api.ts` + `lib/money.ts` (typed client, no UI yet) — commit.
4. Auth shell: `AuthProvider` + Login + `RequireRole` + routing skeleton — commit.
5. Admin reads: dashboard, customers, account detail, invoice detail — commit.
6. Invoice **PDF download** (admin) — commit.
7. Admin billing: generate-one, generate-batch, run status — commit.
8. Customer portal: scoped accounts / invoices / invoice + PDF — commit.
9. Polish: loading/error/empty states, layout + nav — commit.
10. Tag `phase-2-complete`.
