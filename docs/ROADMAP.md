# ROADMAP.md — Build Plan

The phase-by-phase plan. **Do one step at a time.** After each step: run the check, confirm
it passes, `git commit`, then move on. Never let Claude Code build multiple steps at once.

Legend: 🎯 goal · 📂 files · ✅ acceptance check · 💬 prompt to give Claude Code

---

# PHASE 0 — CORE ENGINE  (current)

Goal of the phase: from the database, generate a correct SLT-style PDF bill for any account,
and run it in batch. No API, no frontend, no cloud.

## Step 1 — Project skeleton
🎯 Set up the Python project, config, money helpers, logging, and a passing test.
📂 `pyproject.toml`, `.env.example`, `.gitignore`, `app/__init__.py`,
   `app/core/config.py`, `app/core/money.py`, `app/core/logging.py`, `tests/test_money.py`
✅ `pip install -e .` works; `pytest -q` passes (money rounding test green).
💬 "Do Step 1 from docs/ROADMAP.md. Create the Python project skeleton: pyproject.toml with the
   Phase 0 deps from CLAUDE.md, .env.example, .gitignore, app/core/config.py (pydantic-settings),
   app/core/money.py (Decimal helpers — quantize 2dp ROUND_HALF_UP), app/core/logging.py, and a
   pytest test for the money helper. No DB code yet."

## Step 2 — Database models + migration
🎯 Turn docs/DATABASE.md into SQLAlchemy models and the first Alembic migration.
📂 `app/db/base.py` (engine/session), `app/db/models.py`, `migrations/` (Alembic), `alembic.ini`
✅ `alembic upgrade head` creates all tables + enums in PostgreSQL with no errors.
💬 "Do Step 2 from docs/ROADMAP.md. Implement SQLAlchemy 2.x models for every table and enum in
   docs/DATABASE.md, set up app/db/base.py (engine + session from config), initialise Alembic, and
   generate the first migration. Money columns = Numeric(12,2). Then I'll run alembic upgrade head."

## Step 3 — Seed synthetic data
🎯 Insert realistic fake data, including the verified Sample-1 account.
📂 `app/db/seed.py`
✅ `python -m app.db.seed` inserts 5–10 accounts; the Sample-1 account matches docs/DATABASE.md §7.
💬 "Do Step 3 from docs/ROADMAP.md. Write app/db/seed.py to insert synthetic data: include the exact
   Sample-1 account from docs/DATABASE.md §7, plus 5–9 more accounts of varied shape (single
   sub-account, three sub-accounts, one with a negative discount line, one with zero balance, one with
   carried arrears). Idempotent (safe to re-run). All amounts Decimal."

## Step 4 — Billing engine (no PDF yet)
🎯 Assemble line items and compute the summary into a validated Bill object.
📂 `app/billing/schemas.py` (Pydantic: Bill, BillLine, Summary), `app/billing/repository.py`
   (all SQL), `app/billing/engine.py`, `tests/test_engine.py`
✅ `pytest -q` passes; engine produces **total_payable = 4628.52** for the Sample-1 account.
💬 "Do Step 4 from docs/ROADMAP.md, following docs/BILLING.md. Build Pydantic schemas (Bill/BillLine/
   Summary), app/billing/repository.py (the ONLY file with SQL — fetch account, sub-accounts, line
   items, previous balance, payments), and app/billing/engine.py that computes the summary using the
   formulas in docs/BILLING.md. Add tests asserting the Sample-1 total = 4628.52. Decimal everywhere.
   No FastAPI imports."

## Step 5 — PDF: one hard-coded bill
🎯 Reproduce the Sample-1 INVOICE layout in ReportLab with hard-coded values.
📂 `app/pdf/layout.py` (regions, colors, fonts), `app/pdf/barcodes.py`, `app/pdf/renderer.py`,
   `app/pdf/assets/` (logo + Noto fonts — YOU add these)
✅ Running the renderer produces a PDF that visually matches sample 1 (header band, summary boxes,
   charges table, payment slip, barcode/QR, Sinhala labels render — no tofu).
💬 "Do Step 5 from docs/ROADMAP.md, following docs/PDF.md. Build the ReportLab renderer for the new
   INVOICE layout with HARD-CODED Sample-1 values for now. Register the Noto fonts from app/pdf/assets,
   draw the blue header, the summary boxes, the grouped charges table, the payment slip, and a
   placeholder barcode + QR. Output to ./output/."

## Step 6 — Wire PDF to the engine
🎯 Render from the real Bill object instead of hard-coded values.
📂 `app/pdf/renderer.py`, `app/cli.py` (generate-one)
✅ `python -m app.cli generate-one --account "004 152 4075" --period 2024-02` produces a correct PDF
   end-to-end (DB → engine → PDF).
💬 "Do Step 6 from docs/ROADMAP.md. Replace the hard-coded values in the renderer with fields from the
   Bill object produced by the engine. Add app/cli.py with a generate-one command (typer) that takes
   --account and --period, runs the engine, renders the PDF to ./output/, and persists the invoice."

## Step 7 — Multi-page + variable rows
🎯 Make charges/usage sections flow to extra pages with correct "Page X of N".
📂 `app/pdf/renderer.py`, `app/pdf/layout.py`
✅ A bill with many line items paginates correctly; page counter is right on every page.
💬 "Do Step 7 from docs/ROADMAP.md. Make the charges and usage sections use platypus flowables so long
   bills overflow to page 2+, repeat the header band, and print correct 'Page X of N'."

## Step 8 — Batch run
🎯 Generate bills for all accounts for a period, resiliently.
📂 `app/cli.py` (generate-batch)
✅ `python -m app.cli generate-batch --period 2024-02` writes all PDFs; failures are recorded in
   billing_run_failures and do NOT stop the run; re-running does not duplicate.
💬 "Do Step 8 from docs/ROADMAP.md. Add a generate-batch command that loops all active accounts for a
   period, with per-account try/except, records successes/failures in billing_runs and
   billing_run_failures, is idempotent (unique invoice per account+period), and writes PDFs to ./output/."

## Step 9 — Harden + test
🎯 Cover edge cases and lock behaviour with tests.
📂 `tests/test_engine.py`, `tests/test_pdf_smoke.py`
✅ Tests pass for: no payment, discount-only, zero charges, single vs. multiple sub-accounts; PDF smoke
   test confirms a file is produced.
💬 "Do Step 9 from docs/ROADMAP.md. Add edge-case tests (missing payment, negative-discount-only, zero
   charges, single vs multiple sub-accounts) and a PDF smoke test. Fix anything they expose."

**Phase 0 done = the core engine is complete.** Then create the LATER docs and continue.

---

# LATER PHASES  (create each doc when you reach it)

## Phase 1 — FastAPI backend  → `docs/API.md`
REST endpoints over the engine: list/get invoices, trigger generation, fetch PDF. Pydantic
request/response models. Engine stays untouched (API just calls it).

## Phase 2 — React portals  → `docs/FRONTEND.md`
Vite + TS + Tailwind + shadcn/ui. Admin dashboard (manage customers/packages, trigger billing,
view invoices) and customer portal (view/download bills, history). React Query + Axios.

## Phase 3 — Auth + roles  → `docs/AUTH.md`
JWT (OAuth2 password flow), passlib bcrypt, ADMIN vs CUSTOMER. Customers see only their own
bills. PDFs served via short-lived presigned URLs (not public). PII handling.

## Phase 4 — Scheduler  → `docs/SCHEDULER.md`
Celery + Redis (or APScheduler first). Celery Beat runs the monthly billing job → calls the
same generate-batch logic. Flower for monitoring.

## Phase 5 — Notifications  → `docs/NOTIFICATIONS.md`
Email bill via SES/SMTP (mandatory). SMS/WhatsApp via Twilio (optional). Triggered after a bill
is generated.

## Phase 6 — Docker + AWS  → `docs/DEPLOYMENT.md` + `docs/ARCHITECTURE.md`
Dockerfiles + docker-compose. GitHub Actions CI/CD → ECR. Deploy: ECS Fargate (API), RDS
PostgreSQL, ElastiCache Redis, S3 (PDFs + frontend), CloudFront, SES, ALB, Route 53, ACM.
CloudWatch logs/alarms, Secrets Manager, Terraform for IaC.

---

## Manual to-dos (you, not Claude Code)

- Before Step 2: install + run **PostgreSQL**, create the `slt_ebill` database.
- Before Step 5: place the **SLT/Mobitel logo** and **Noto Sans Sinhala/Tamil fonts** in
  `app/pdf/assets/`.
- Each later phase: create its `docs/*.md` (ask for it) before prompting Claude Code to build it.
