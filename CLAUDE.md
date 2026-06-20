# CLAUDE.md — SLT E-Bill System

Lean project index for Claude Code. Read this first. Detailed specs live in `docs/` — open
the relevant one only when working on that area (keeps context small).

---

## What we're building

A production-style telecom billing system that generates SLT-style PDF e-bills from a
database, one per account, in batch. Full system eventually = DB + billing engine + PDF +
FastAPI + React portals + auth + scheduler + notifications + AWS. **Build in phases.**

**Current phase: Phase 0 — Core Engine only** (DB → billing engine → PDF → batch CLI).
Everything else is LATER. Do not build API/frontend/AWS yet.

---

## Non-negotiable rules

1. **Money = `Decimal`**, quantized 2 dp, `ROUND_HALF_UP`. Never `float`. DB uses `NUMERIC(12,2)`.
2. **Billing logic is framework-independent.** No FastAPI/HTTP imports in the engine. Runs via
   CLI or plain import. Unit-testable without a server.
3. **Batch runs are idempotent.** One bill per account per period (DB unique constraint).
   One account failing must NOT stop the run — log it, record the failure, continue.
4. **An invoice is a frozen snapshot.** Store computed totals; never recompute past bills.
5. **No PII in logs or git.** All seed data is synthetic.
6. **Engine + renderer depend on the validated `Bill` object, never on raw DB rows.**
   All SQL lives in `app/billing/repository.py` — the only file that changes when we later
   swap to SLT's real database.

---

## The real billing math (verified against sample bills)

```
charges_for_period = sum(all line items, tax included, discounts negative)
arrears            = balance_bf - payments_received
total_payable      = arrears + charges_for_period
```
The supervisor doc's `base + 15% tax` formula is WRONG — ignore it. Use the above.

---

## Tech stack (Phase 0)

- Language: Python 3.11+ · DB: PostgreSQL 15+
- ORM/migrations: SQLAlchemy 2.x + Alembic · Validation: Pydantic v2 + pydantic-settings
- PDF: ReportLab + qrcode + python-barcode + Pillow
- Fonts: Noto Sans + Noto Sans Sinhala/Tamil (embedded) · CLI: typer · Tests: pytest

Later phases add: FastAPI, React+Vite+TS, JWT auth, Celery+Redis, AWS (ECS/RDS/S3/SES), Docker.

---

## Docs map (where the detail is)

| Topic | File |
|---|---|
| Phase plan + step order ("what's next") | `docs/ROADMAP.md` |
| Database schema + seed | `docs/DATABASE.md` |
| Billing engine logic + math | `docs/BILLING.md` |
| PDF layout, fonts, assets | `docs/PDF.md` |
| (later) system + AWS, API, frontend, deploy | `docs/ARCHITECTURE.md`, `API.md`, `FRONTEND.md`, `DEPLOYMENT.md` |

---

## Project layout (target — Claude Code generates code dirs)

```
app/
  core/     config.py, money.py, logging.py
  db/       base.py, models.py, seed.py
  billing/  engine.py, schemas.py, repository.py
  pdf/      renderer.py, layout.py, barcodes.py, assets/
  cli.py
migrations/   tests/   output/   pyproject.toml   .env.example
```

---

## How to work

Do ONE roadmap step at a time. After each: run tests / migrations, confirm it works, commit,
then next. Never build multiple phases at once. Verify the engine total = **4628.52** (the
DATABASE.md seed) before any PDF work.

---

## Confirmed decisions

| Decision | Choice |
|---|---|
| Data source | Our own PostgreSQL + synthetic seed; swap to SLT later via `repository.py` |
| Target layout | New "INVOICE" format (sample 1) |
| Engine v1 | Assemble stored line items + compute summary |
| Sinhala/Tamil | Embed Noto fonts |
| Logo | Real SLT/Mobitel logo → `app/pdf/assets/` |
| Barcode/QR | Placeholder for v1; real spec later |
| Taxes | Stored figure for v1; real rate later |
| PDF tech | ReportLab |
