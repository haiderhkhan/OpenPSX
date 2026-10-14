# P8-04: local backup launcher. Runs the whole app on this laptop: backend :8000, frontend :3000.
# Usage (from anywhere):  powershell -ExecutionPolicy Bypass -File "<repo>\scripts\run_local.ps1" [-SkipBuild]
# Works offline once one build has succeeded: verdicts come from the seed, other LLM text from templates.
# Windows PowerShell 5.1: no && / ?? operators. Every path is quoted, so a space in the repo path is fine (D-22).
param(
    [switch]$SkipBuild  # reuse the last frontend build (e.g. Wi-Fi off: next/font needs the network to build)
)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Frontend = Join-Path $Root 'frontend'
$Python = Join-Path $Root '.venv\Scripts\python.exe'  # the venv's own python = an activated .venv
$Api = 'http://127.0.0.1:8000'
$Web = 'http://localhost:3000'

function Test-Port([int]$Port) {
    return [bool](Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
}

function Wait-Url([string]$Url, [int]$Seconds) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        try {
            Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5 | Out-Null
            return $true
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    return $false
}

function Start-Window([string]$Title, [string]$Dir, [string]$Command) {
    # A new PowerShell window that stays open; single quotes in paths are doubled for the inner command.
    $dirArg = $Dir.Replace("'", "''")
    $inner = "`$Host.UI.RawUI.WindowTitle = '$Title'; Set-Location -LiteralPath '$dirArg'; $Command"
    Start-Process powershell -ArgumentList @('-NoExit', '-ExecutionPolicy', 'Bypass', '-Command', $inner)
}

if (-not (Test-Path -LiteralPath $Python)) { throw "No .venv at $Root. Create it and pip install -r requirements.txt first." }
if (Test-Port 3000) { throw "Port 3000 is in use (a Next.js dev server?). Stop it first: next build and next dev share .next." }

# 1-2. Backend on 8000 in its own window (reuse one that is already running).
if (Test-Port 8000) {
    Write-Host "Backend already listening on 8000; reusing it."
} else {
    $py = $Python.Replace("'", "''")
    Start-Window 'OPEN PSX backend :8000' $Root "& '$py' -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"
}
if (-not (Wait-Url "$Api/api/health" 60)) { throw "Backend did not answer $Api/api/health within 60 s; see its window." }
Write-Host "Backend up: $Api/api/health"

# 3. frontend/.env.local for localhost, only if missing (NEXT_PUBLIC_* values are baked in at build time).
$envLocal = Join-Path $Frontend '.env.local'
if (-not (Test-Path -LiteralPath $envLocal)) {
    Set-Content -LiteralPath $envLocal -Encoding ascii -Value @("NEXT_PUBLIC_API_BASE=$Api", 'NEXT_PUBLIC_USE_MOCKS=false')
    Write-Host "Wrote frontend/.env.local for localhost."
}

# 4. Build (fall back to the last good build when offline), then start on 3000 in its own window.
Push-Location -LiteralPath $Frontend
try {
    if (-not (Test-Path -LiteralPath (Join-Path $Frontend 'node_modules'))) { npm install }
    if (-not $SkipBuild) {
        npm run build
        if ($LASTEXITCODE -ne 0) {
            if (Test-Path -LiteralPath (Join-Path $Frontend '.next\BUILD_ID')) {
                Write-Warning "npm run build failed (offline?); starting the previous build instead."
            } else {
                throw "npm run build failed and there is no previous build to start."
            }
        }
    }
} finally {
    Pop-Location
}
Start-Window 'OPEN PSX frontend :3000' $Frontend 'npm run start -- --port 3000'
if (-not (Wait-Url $Web 90)) { throw "Frontend did not answer $Web within 90 s; see its window." }

# 5. Open the browser.
Start-Process $Web
Write-Host "OPEN PSX is running: $Web (API $Api). Close the two windows to stop it."
