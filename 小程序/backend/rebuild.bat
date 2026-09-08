@echo off
setlocal enabledelayedexpansion

set COMPOSE=compose -f docker-compose.yml -f docker-compose.windows.yml
set SERVICE_NAME=live_core_service

echo ========================================
echo   Rebuild Live Core Service (Windows)
echo ========================================

if "%1"=="-c" goto full_rebuild
if "%1"=="--clean" goto full_rebuild
goto service_rebuild

:full_rebuild
echo [Full rebuild] Stopping all services and removing pgdata volume...
docker %COMPOSE% down -v
docker %COMPOSE% build --no-cache %SERVICE_NAME% celery_worker
docker %COMPOSE% up -d
goto done

:service_rebuild
echo [Service rebuild] Rebuilding %SERVICE_NAME% and celery_worker...
docker %COMPOSE% stop %SERVICE_NAME% celery_worker
docker %COMPOSE% build --no-cache %SERVICE_NAME% celery_worker
docker %COMPOSE% up -d %SERVICE_NAME% celery_worker
goto done

:done
echo.
docker %COMPOSE% ps
echo.
echo Done. Logs: docker %COMPOSE% logs -f %SERVICE_NAME%
pause
