@echo off
setlocal
cd /d "%~dp0\.."

where docker >nul 2>&1
if errorlevel 1 (
  echo ERROR: Docker is not installed or is not available on PATH.
  exit /b 1
)

docker compose down --remove-orphans
if errorlevel 1 exit /b 1
echo FinAgent Platform stopped. Named data volumes were preserved.
exit /b 0
