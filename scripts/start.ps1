<# start.ps1 — Start Green Grid Platform locally #>

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$src  = Join-Path $root "src"
$venv = Join-Path $src ".venv\Scripts\Activate.ps1"

Write-Host "`n=== 1. Starting Docker services (Postgres + Redis) ===" -ForegroundColor Cyan
docker compose -f (Join-Path $root "docker-compose.yml") up -d

Write-Host "`n=== 2. Activating virtual environment ===" -ForegroundColor Cyan
& $venv

Write-Host "`n=== 3. Running migrations ===" -ForegroundColor Cyan
Push-Location $src
& python manage.py migrate --noinput

Write-Host "`n=== 4. Starting Django dev server on http://localhost:8000 ===" -ForegroundColor Cyan
& python manage.py runserver 0.0.0.0:8000
Pop-Location
