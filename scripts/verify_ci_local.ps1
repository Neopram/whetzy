<#
.SYNOPSIS
    Replicates .github/workflows/ci.yml locally — backend + frontend jobs.
    E2E job requires Docker+Postgres (unavailable on this PC); logs CI-LOCAL.
    Writes full log to scratchpad; exits 0 only if all runnable steps pass.

.NOTES
    Mirrors ci.yml step order exactly. Run from the repo root.
    Usage: pwsh scripts/verify_ci_local.ps1
#>
param(
    [switch]$SkipPipAudit,   # skip pip-audit network check (offline)
    [switch]$SkipNpmAudit,   # skip npm audit network check (offline)
    [switch]$SkipE2E         # always set locally (no Docker/Postgres)
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

$Root  = Split-Path $PSScriptRoot -Parent
$Scratch = if ($env:CLAUDE_SCRATCHPAD) { $env:CLAUDE_SCRATCHPAD }
           else { Join-Path $env:TEMP "whetzy_ci_local" }
New-Item -ItemType Directory -Force $Scratch | Out-Null
$LogFile = Join-Path $Scratch "ci_local_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
$StartTime = Get-Date

$Steps = [System.Collections.Generic.List[hashtable]]::new()
$Failures = [System.Collections.Generic.List[string]]::new()

function Log([string]$msg) {
    $ts = (Get-Date).ToString('HH:mm:ss')
    $line = "[$ts] $msg"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line
}

function Step([string]$name, [scriptblock]$cmd, [bool]$skip=$false, [string]$skipReason='') {
    if ($skip) {
        Log "SKIP  $name — $skipReason"
        $Steps.Add(@{Name=$name; Status='SKIP'; Duration=0})
        return
    }
    Log "RUN   $name"
    $t0 = Get-Date
    try {
        $out = & $cmd 2>&1
        $ex  = $LASTEXITCODE
    } catch {
        $out = $_.Exception.Message; $ex = 1
    }
    $dur = [int]((Get-Date) - $t0).TotalSeconds
    $outStr = ($out | Out-String).Trim()
    Add-Content -Path $LogFile -Value $outStr
    if ($ex -ne 0) {
        Log "FAIL  $name (exit $ex, ${dur}s)"
        $Failures.Add($name)
        $Steps.Add(@{Name=$name; Status='FAIL'; Duration=$dur})
        # Print last 8 lines for visibility
        $outStr -split "`n" | Select-Object -Last 8 | ForEach-Object { Write-Host "      $_" }
    } else {
        Log "PASS  $name (${dur}s)"
        $Steps.Add(@{Name=$name; Status='PASS'; Duration=$dur})
    }
}

Log "=== verify_ci_local.ps1 — $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="
Log "Log: $LogFile"
Log ""

# ── BACKEND JOB ────────────────────────────────────────────────────────────────
Log "--- JOB: backend ---"

$env:DATABASE_URL   = "sqlite+aiosqlite:///:memory:"
$env:ENVIRONMENT    = "test"
$env:SECRET_KEY     = "ci-secret-key-not-for-production-0123456789abcdef"
$env:GROQ_API_KEY   = ""
$env:COVERAGE_FILE  = Join-Path $Scratch ".coverage_whetzy"

$BackendDir = Join-Path $Root "backend"

Step "backend: pip install" {
    Set-Location $BackendDir
    python -m pip install --upgrade pip --quiet
    python -m pip install -r requirements.txt pip-audit pytest-cov mypy ruff --quiet
}

Step "backend: pip-audit" {
    Set-Location $BackendDir
    pip-audit --progress-spinner off `
      --ignore-vuln PYSEC-2026-161 `
      --ignore-vuln PYSEC-2026-248 `
      --ignore-vuln PYSEC-2026-249 `
      --ignore-vuln PYSEC-2026-1942 `
      --ignore-vuln PYSEC-2026-1941 `
      --ignore-vuln PYSEC-2026-2281 `
      --ignore-vuln PYSEC-2026-2280 `
      --ignore-vuln PYSEC-2026-1325
} -skip:$SkipPipAudit -skipReason:"--SkipPipAudit flag set"

Step "backend: check_question_bank" {
    Set-Location $Root
    python scripts/check_question_bank.py
}

Step "backend: ruff" {
    Set-Location $BackendDir
    ruff check app tests
}

Step "backend: mypy" {
    Set-Location $BackendDir
    mypy app --strict --ignore-missing-imports
}

Step "backend: pytest" {
    Set-Location $BackendDir
    python -m pytest tests/ --tb=short -q `
      --cov=app --cov-report=term-missing --cov-fail-under=80
}

# ── FRONTEND JOB ───────────────────────────────────────────────────────────────
Log ""
Log "--- JOB: frontend ---"

$FrontendDir = Join-Path $Root "frontend"
Set-Location $FrontendDir

Step "frontend: npm ci" {
    Set-Location $FrontendDir
    npm ci --prefer-offline 2>&1
}

Step "frontend: npm audit" {
    Set-Location $FrontendDir
    npm audit --audit-level=high
} -skip:$SkipNpmAudit -skipReason:"--SkipNpmAudit flag set"

Step "frontend: tsc -b" {
    Set-Location $FrontendDir
    npx tsc -b 2>&1
}

Step "frontend: oxlint" {
    Set-Location $FrontendDir
    npx oxlint src --deny-warnings 2>&1
}

Step "frontend: test:coverage (vitest)" {
    Set-Location $FrontendDir
    npm run test:coverage 2>&1
}

Step "frontend: build" {
    Set-Location $FrontendDir
    npm run build 2>&1
}

Step "frontend: check-prerender" {
    Set-Location $FrontendDir
    node scripts/check-prerender.mjs 2>&1
}

Step "frontend: check-bundle" {
    Set-Location $FrontendDir
    node scripts/check-bundle.mjs 2>&1
}

Step "frontend: check-no-third-party" {
    Set-Location $FrontendDir
    node scripts/check-no-third-party.mjs 2>&1
}

# ── E2E JOB — SKIP (Docker/Postgres unavailable locally) ──────────────────────
Log ""
Log "--- JOB: e2e ---"
Step "e2e: migrate+seed+playwright" {} -skip:$true -skipReason:"Needs Docker+Postgres (H.13/H.17). CI-LOCAL: mark as untested locally."

# ── SUMMARY ───────────────────────────────────────────────────────────────────
$Duration = [int]((Get-Date) - $StartTime).TotalSeconds
Log ""
Log "=== SUMMARY (${Duration}s) ==="
foreach ($s in $Steps) {
    $icon = @{PASS='✓'; FAIL='✗'; SKIP='–'}[$s.Status]
    Log ("  $icon  {0,-40} {1}" -f $s.Name, $s.Status)
}
Log ""

$RunCount  = ($Steps | Where-Object { $_.Status -ne 'SKIP' }).Count
$PassCount = ($Steps | Where-Object { $_.Status -eq 'PASS' }).Count
$FailCount = $Failures.Count

if ($FailCount -eq 0) {
    Log "RESULT: PASS — $PassCount/$RunCount steps OK (CI-LOCAL $(Get-Date -Format 'yyyy-MM-dd') exit 0)"
    Write-Host ""
    Write-Host "CI-LOCAL $(Get-Date -Format 'yyyy-MM-dd') exit 0" -ForegroundColor Green
    Set-Location $Root
    exit 0
} else {
    Log "RESULT: FAIL — $FailCount failures: $($Failures -join ', ')"
    Write-Host ""
    Write-Host "CI-LOCAL $(Get-Date -Format 'yyyy-MM-dd') exit 1 — failures: $($Failures -join ', ')" -ForegroundColor Red
    Set-Location $Root
    exit 1
}
