# SLT E-Bill System

A production-style telecom billing system that generates SLT-style PDF e-bills from a
PostgreSQL database — one bill per account, runnable in batch.

Built in phases. **Phase 0 (current): the core engine** — database → billing engine → PDF →
batch CLI. Later phases add a FastAPI backend, React admin/customer portals, authentication,
an automated monthly scheduler, email/SMS notifications, and AWS deployment.

> Contributor/AI guide: see `CLAUDE.md`. Detailed specs: see `docs/`.

> Current status: Phases 0-4 are implemented (engine/PDF/CLI, API, frontend,
> auth/roles, and scheduler). Phase 5 notifications are partially implemented:
> manual outbox/CLI sending exists, and scheduled Celery delivery is being finished.
> Phase 6 deployment/AWS is intentionally not started yet.

---

## Prerequisites (install before you start)

- **Python 3.11+**
- **PostgreSQL 15+** (the database server must be running)
- **Git**
- Fonts (for the PDF phase): Noto Sans, Noto Sans Sinhala, Noto Sans Tamil
  (free from Google Fonts → place in `app/pdf/assets/`)
- SLT/Mobitel logo (for the PDF phase) → `app/pdf/assets/`

---

## Setup

```bash
# 1. clone / open the project
cd slt-billing-system

# 2. create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. install dependencies (after Step 1 creates pyproject.toml)
pip install -e .

# 4. configure environment
cp .env.example .env             # then edit DB credentials in .env

# 5. create the database (in PostgreSQL)
createdb slt_ebill               # or via psql / pgAdmin

# 6. run migrations to create tables
alembic upgrade head

# 7. seed synthetic data
python -m app.db.seed
```

---

## Usage

```bash
# generate one bill by account number
python -m app.cli generate-one --account "004 152 4075" --period 2024-02

# generate all bills for a billing period (batch run)
python -m app.cli generate-batch --period 2024-02

# generated PDFs land in ./output/
```

---

## Tests

```bash
pytest -q
```

The billing engine is tested against a known sample bill — the seed account in
`docs/DATABASE.md` must produce a total payable of **4628.52**.

---

## Project structure

```
slt-billing-system/
├── CLAUDE.md            # AI/contributor index (auto-loaded by Claude Code)
├── README.md           # this file
├── docs/               # detailed specs (database, billing, pdf, roadmap, ...)
├── app/
│   ├── core/           # config, money (Decimal), logging
│   ├── db/             # SQLAlchemy models, session, seed
│   ├── billing/        # engine, schemas, repository (all SQL lives here)
│   ├── pdf/            # ReportLab renderer, layout, barcodes, assets
│   └── cli.py          # generate-one / generate-batch
├── migrations/         # Alembic
├── tests/
├── output/             # generated PDFs (gitignored)
├── pyproject.toml
└── .env.example
```

---

## Key design rules

- Money is `Decimal` (DB `NUMERIC`), never `float`.
- Billing logic is independent of the API/web layer (testable standalone).
- Batch runs are idempotent; one failed bill never stops the run.
- All database access lives in `app/billing/repository.py`, so swapping to SLT's real
  database later means changing only that file.

See `CLAUDE.md` and `docs/` for the full rationale and the phase roadmap.

---

## Status

- [x] Database schema designed (`docs/DATABASE.md`)
- [x] Phase 0: core engine (DB code, billing engine, PDF, batch CLI)
- [x] Phase 1: FastAPI backend
- [x] Phase 2: React portals
- [x] Phase 3: auth + roles
- [x] Phase 4: scheduler (auto billing)
- [ ] Phase 5: notifications (manual outbox/CLI complete; scheduled Celery delivery in progress)
- [ ] Phase 6: Docker + AWS deployment
