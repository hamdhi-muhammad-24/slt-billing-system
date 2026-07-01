[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BaseUrl,
    [string]$AdminEmail = "",
    [string]$AdminPassword = "",
    [int]$TimeoutSeconds = 20
)

$ErrorActionPreference = "Stop"

function Join-Url {
    param(
        [string]$Root,
        [string]$Path
    )

    return "$($Root.TrimEnd('/'))/$($Path.TrimStart('/'))"
}

function Write-Pass {
    param([string]$Message)
    Write-Host "[PASS] $Message"
}

function Write-Skip {
    param([string]$Message)
    Write-Host "[SKIP] $Message"
}

$BaseUrl = $BaseUrl.TrimEnd("/")

Write-Host "Phase 6G smoke test for $BaseUrl"

$healthUrl = Join-Url -Root $BaseUrl -Path "/health"
$health = Invoke-RestMethod -Method Get -Uri $healthUrl -TimeoutSec $TimeoutSeconds
if ($health.status -ne "ok") {
    throw "Health check returned unexpected status: $($health | ConvertTo-Json -Compress)"
}
Write-Pass "API health check returned ok"

if (-not [string]::IsNullOrWhiteSpace($AdminEmail) -and -not [string]::IsNullOrWhiteSpace($AdminPassword)) {
    $loginUrl = Join-Url -Root $BaseUrl -Path "/auth/login"
    $loginBody = @{
        username = $AdminEmail
        password = $AdminPassword
    }
    $login = Invoke-RestMethod -Method Post -Uri $loginUrl -ContentType "application/x-www-form-urlencoded" -Body $loginBody -TimeoutSec $TimeoutSeconds
    if ([string]::IsNullOrWhiteSpace($login.access_token)) {
        throw "Login did not return an access token."
    }
    Write-Pass "Admin login returned an access token"

    $meUrl = Join-Url -Root $BaseUrl -Path "/auth/me"
    $headers = @{ Authorization = "Bearer $($login.access_token)" }
    $me = Invoke-RestMethod -Method Get -Uri $meUrl -Headers $headers -TimeoutSec $TimeoutSeconds
    if ($me.role -ne "ADMIN") {
        throw "Expected ADMIN role, got $($me.role)."
    }
    Write-Pass "Authenticated /auth/me returned ADMIN user"
}
else {
    Write-Skip "Admin login check. Re-run with -AdminEmail and -AdminPassword when you are ready."
}

Write-Host ""
Write-Host "Manual checks to finish in the browser:"
Write-Host "1. Open $BaseUrl and confirm the React app loads."
Write-Host "2. Log in as admin."
Write-Host "3. Generate one bill for a known account and period."
Write-Host "4. Download the generated PDF."
Write-Host "5. Check that the PDF object exists in the production S3 PDF bucket."
Write-Host "6. Confirm notification rows are queued/sent as expected."
Write-Host "7. Open CloudWatch Logs for /ecs/slt-backend, /ecs/slt-worker, and /ecs/slt-beat."
