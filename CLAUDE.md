# CLAUDE.md — SLT E-Bill System
# ============================================================
# READ THIS FILE FIRST BEFORE MAKING ANY CHANGES
# This file is the single source of truth for the current
# state of the project. Always read it before starting any task.
# ============================================================

## What We Have Built

A **fully deployed production telecom billing system** for SLT (Sri Lanka Telecom) that generates PDF e-bills from GMF (billing data files) in batch. The system is live on a production VM and also runs locally.

**System is COMPLETE and DEPLOYED. All core phases are done. Current work is iterative improvements.**

---

## Architecture Overview

```
frontend/           React + Vite + Tailwind — Admin UI (port 8080 in prod, 5173 in dev)
app/
  api/routers/      FastAPI HTTP layer — thin, only validates + calls services
  billing/          Core billing engine: worker_queue.py, gmf_core/, batch.py
  uploads/          watcher.py — Watchdog-based filesystem watcher for incoming GMFs
  db/               models.py, seed.py, base.py (PostgreSQL via SQLAlchemy)
  auth/             JWT auth (admin / admin1 / customer roles)
  core/             config.py (Settings via .env), logging, money
  scheduler/        Celery + Redis for scheduled billing runs
migrations/         Alembic migration versions
Models/SmartAI_Bill/  The AI billing engine
  templates/        template registry + per-template parser + renderer
    nonvat_home/           ACTIVE
    nonvat_enterprise/     ACTIVE
    vat_home/              ACTIVE
    vat_enterprise/        ACTIVE
    product_label_grouping/ ACTIVE
    subscription_ref_grouping/ ACTIVE
    summary_statement/     ACTIVE
    invoice_of_summary/    ACTIVE (recently enabled)
    vat_creditnote/        ACTIVE
    nonvat_creditnote/     ACTIVE
docker-compose.prod.yml  Production Docker Compose
docker-compose.yml       Dev Compose (only Redis + Mailpit)
```

---

## Two Deployments

### 1. Local Development (Windows)
- **Start command:** `.\start.ps1`
- **Frontend:** `http://localhost:5173`
- **Backend API:** `http://localhost:8090`
- **GMF Uploads Path:** `G:/My Drive/SLT_GMF_Uploads` (Google Drive mounted locally)
- **Output PDFs:** `./output`
- **Database:** PostgreSQL on localhost:5432
- **Redis:** Docker on port 16379

### 2. Production VM (SLM-EKB)
- **IP:** `206.189.159.175`
- **SSH:** `ssh root@206.189.159.175`
- **Project folder on VM:** `/root/slt-billing`
- **Frontend:** `http://206.189.159.175:8080`
- **Backend API:** `http://206.189.159.175:8000`
- **GMF Uploads Path (on VM host):** `/var/slt-billing/gmf_uploads` -> mapped to `/app/gmf_uploads` inside containers
- **Output PDFs (on VM host):** `/var/slt-billing/output_invoices` -> mapped to `/app/output` inside containers
- **Google Drive Sync:** `rclone` syncs `/var/slt-billing/output_invoices` -> `gdrive:SLT_Output_Invoices` every 5 minutes via cronjob
- **Services managed by:** Docker Compose (`docker-compose.prod.yml`)
- **Other projects on VM (DO NOT TOUCH):** `langfuse` (port 3000), `ai_agents` (ports 8100/3100)

---

## User Accounts

| Email | Password | Role | Notes |
|---|---|---|---|
| `admin@slt.lk` | `admin123` | ADMIN | Full admin access |
| `admin1@slt.lk` | `admin1123` | ADMIN1 | File upload + monitoring only |

---

## Key Files Changed Recently (July 2026)

### Bug Fixes
- **`app/billing/worker_queue.py`** — Fixed race condition in status updates. Added `_robust_file_op()` retry wrapper for Windows file locking (WinError 32). Fixed atomic DB increment to avoid lost updates.
- **`app/api/routers/billing.py`** — Fixed duplicate upload bug by reversing sequence: DB commit -> disk write.
- **`app/uploads/watcher.py`** — Fixed watcher race condition caused by old file-first sequence.
- **`reset_test_data.py`** — Added comprehensive filesystem cleanup (queue folders, output, drive subdirs).

### UI Improvements
- **`frontend/src/pages/admin/GenerationHub.tsx`** — Added `shrink-0` to RunCard to fix overlapping cards when list grows.
- **`frontend/src/pages/admin/InvoicePreview.tsx`** — Updated mode selector buttons (Auto/Manual) to premium dark/light gradient. Updated "Generate PDF Preview" button to match. Template name badge changed to amber/yellow for clear visibility.
- **`frontend/src/pages/admin/GmfMonitor.tsx`** — Added "Show Completed" toggle switch.
- **`frontend/src/pages/admin/UploadCenter.tsx`** — Added GMF file format validation (rejects non-GMF files).
- **`frontend/src/components/AdminLayout.tsx`** — Cleaned sidebar navigation.

### Infrastructure
- **`docker-compose.prod.yml`** — Updated all volume mounts to use `/var/slt-billing/` paths and added output volume for persistent storage.
- **`Models/SmartAI_Bill/templates/registry.py`** — Set `invoice_of_summary` to `ready: True`.

---

## VM Deployment Commands (Reference)

### Update & Redeploy to VM
```bash
# On LOCAL machine: commit + push
git add .
git commit -m "your message"
git push origin main

# On VM SSH terminal:
cd slt-billing
git pull origin main
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up --build -d
```

### Run Database Migrations on VM
```bash
docker exec -it slt-billing-backend-1 alembic upgrade head
```

### Re-Seed Users on VM (if admin1 login fails)
```bash
docker exec -it slt-billing-backend-1 python -m app.db.seed
```

### Reset All Test Data on VM (Clean Slate for Testing)
```bash
docker exec -it slt-billing-backend-1 python reset_test_data.py
# Type YES when prompted

# Then clear Google Drive output folder immediately:
rclone sync /var/slt-billing/output_invoices gdrive:SLT_Output_Invoices
```

---

## Important Conventions

1. **Money = `Decimal`**, quantized 2 dp, `ROUND_HALF_UP`. Never `float`.
2. **Billing logic is framework-independent.** No FastAPI/HTTP imports in the engine.
3. **API is a thin layer.** No billing math or SQL inside routers.
4. **Batch runs are idempotent.** One bill per account per period.
5. **An invoice is a frozen snapshot.** Store computed totals, never recompute.
6. **No PII in logs or git.** All test data is synthetic.

---

## What Needs To Be Done Next (Open Tasks)

1. **Subdomain Setup:** `VITE_API_BASE_URL` in `docker-compose.prod.yml` is hardcoded to `http://206.189.159.175:8000`. When a subdomain is configured, update this and rebuild containers. Also update `CORS_ORIGINS` in backend environment.
2. **Admin1 Portal Branding:** The phrase "Admin 1 portal for file uploads and monitoring" still appears in some UI headers. Should be replaced with "This portal" or a cleaner label.
3. **Billing Operator Persona Naming:** Give a professional name to the "Billing Operator" (Admin1) persona.

---

## GitHub Repository

- **Repo:** `https://github.com/hamdhi-muhammad-24/slt-billing-system` (PUBLIC)
- **Branch:** `main`
- **Latest commit:** All July 2026 bug fixes, UI improvements, and VM deployment config are pushed and live.