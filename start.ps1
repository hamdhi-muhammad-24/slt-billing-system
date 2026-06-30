# start.ps1 — One-command startup for SLT Billing System
# Usage:
#   .\start.ps1           — start all services (Docker + API + Frontend)
#   .\start.ps1 --setup   — run DB migrations + seed first, then start all

param(
    [switch]$setup
)

$ProjectRoot = $PSScriptRoot
$VenvActivate = "$ProjectRoot\.venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "=== SLT Billing System — Starting Up ===" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Docker (Redis + Mailpit) ──────────────────────────────────────────
Write-Host '[1/3] Starting Docker services (Redis + Mailpit)...' -ForegroundColor Yellow
Set-Location $ProjectRoot
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker failed to start. Is Docker Desktop running?" -ForegroundColor Red
    exit 1
}
Write-Host "      Docker services running." -ForegroundColor Green
Write-Host ""

# ── Step 2 (optional): DB setup ───────────────────────────────────────────────
if ($setup) {
    Write-Host "[--setup] Running DB migrations and seed..." -ForegroundColor Yellow

    & $VenvActivate
    python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: alembic upgrade failed." -ForegroundColor Red; exit 1 }

    python -m app.db.seed
    if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: app.db.seed failed." -ForegroundColor Red; exit 1 }

    python -m app.auth.seed
    if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: app.auth.seed failed." -ForegroundColor Red; exit 1 }

    Write-Host "      DB ready." -ForegroundColor Green
    Write-Host ""
}

# ── Step 3: FastAPI backend (new window) ──────────────────────────────────────
Write-Host "[2/3] Starting FastAPI backend on http://localhost:8000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$ProjectRoot'; & '$VenvActivate'; uvicorn app.api.main:app --reload --port 8000"
) -WindowStyle Normal
Write-Host "      FastAPI window opened." -ForegroundColor Green
Write-Host ""

# ── Step 4: React frontend (new window) ───────────────────────────────────────
Write-Host "[3/3] Starting React frontend on http://localhost:5173 ..." -ForegroundColor Yellow
$stale = (Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue).OwningProcess
if ($stale) {
    Write-Host "      Killing stale process on port 5173 (PID $stale)..." -ForegroundColor DarkGray
    Stop-Process -Id $stale -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
}
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$ProjectRoot\frontend'; npm run dev"
) -WindowStyle Normal
Write-Host "      React window opened." -ForegroundColor Green
Write-Host ""

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host "=== All services starting ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Frontend   ->  http://localhost:5173" -ForegroundColor White
Write-Host "  API        ->  http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs   ->  http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Mailpit    ->  http://localhost:8025" -ForegroundColor White
Write-Host ""
Write-Host "Wait ~5 seconds for the frontend to compile, then open your browser." -ForegroundColor DarkGray
Write-Host ""
