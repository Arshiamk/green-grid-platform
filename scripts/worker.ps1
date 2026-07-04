<# worker.ps1 — Start Celery worker #>

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$src  = Join-Path $root "src"
$venv = Join-Path $src ".venv\Scripts\Activate.ps1"

Write-Host "`n=== Starting Celery worker ===" -ForegroundColor Cyan
& $venv
Push-Location $src
& celery -A config worker --loglevel=info --pool=solo
Pop-Location
