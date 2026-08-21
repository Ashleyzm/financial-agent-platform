@echo off
setlocal
cd /d "%~dp0\.."

where docker >nul 2>&1
if errorlevel 1 (
  echo ERROR: Docker is not installed or is not available on PATH.
  exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
  echo ERROR: Docker Desktop is not running.
  exit /b 1
)

if not exist ".env" (
  copy /Y ".env.example" ".env" >nul
  echo Created .env from .env.example.
)

echo Starting FinAgent Platform and waiting for service health checks...
docker compose up -d --build --wait
if errorlevel 1 exit /b 1

docker compose exec -T api python -c "import urllib.request; assert urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=10).status == 200"
if errorlevel 1 exit /b 1
docker compose exec -T web wget -qO- http://127.0.0.1/ >nul
if errorlevel 1 exit /b 1

echo FinAgent Platform is healthy.
docker compose ps
exit /b 0
