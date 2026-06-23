# SCHEDULER.md — Phase 4 (Scheduler)

NEW layer that CALLS existing batch logic. Never edits engine/repository/PDF/API/auth (FROZEN).
Runs the monthly billing automatically. Anchor unchanged: 004 152 4075 = 4628.52.

## Scope
IN: extract batch into a reusable service; Celery task; Redis broker (Docker); Celery Beat
monthly schedule; Flower monitoring.
OUT: email/SMS (Phase 5); app Docker image / AWS / ECS / ElastiCache (Phase 6).
The monthly job GENERATES PDFs and stops there.

## Local infra
Redis in Docker (production-identical). Worker/Beat/Flower run on Windows for dev.
Windows: Celery worker MUST use --pool=solo (dev-only; Linux/ECS uses default).
docker-compose.yml (repo root): redis:7-alpine on 6379 with a named volume.

## New files
app/billing/batch.py        # run_billing_batch() — loop extracted from cli.py
app/scheduler/__init__.py
app/scheduler/celery_app.py  # Celery instance (broker/backend=Redis) + Beat schedule
app/scheduler/tasks.py       # ping + run_monthly_billing
docker-compose.yml
Config (ADDITIVE): CELERY_BROKER_URL=redis://localhost:6379/0,
CELERY_RESULT_BACKEND=redis://localhost:6379/1 in core/config.py + .env.example.
Deps (Phase 4): celery, redis, flower.

## Chunks
A — Extract batch loop into app/billing/batch.py; CLI becomes a thin caller. Behavior identical.
B — docker-compose Redis + Celery app + ping task.
C — run_monthly_billing task wraps run_billing_batch.
D — Beat monthly schedule + Flower. Then tag phase-4-complete.