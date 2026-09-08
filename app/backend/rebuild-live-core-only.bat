@echo off
REM Rebuild live_core_service database only (preserve other databases)

set COMPOSE_FILE=compose-app.windows.yml
set SERVICE_NAME=live_core_service
set DB_NAME=live_core_test

echo === Rebuild live_core_service database only ===
echo [WARN] This will delete %DB_NAME% database, but preserve other databases (media_download_test, users_service_test)
echo.
set /p confirm="Continue? (y/N): "
if /i not "%confirm%"=="y" (
    echo Cancelled
    exit /b 1
)

echo 1. Stopping live_core_service and celery_worker...
docker-compose -f %COMPOSE_FILE% stop %SERVICE_NAME% celery_worker

echo 2. Dropping %DB_NAME% database...
docker-compose -f %COMPOSE_FILE% exec -T postgres psql -U postgres -c "DROP DATABASE IF EXISTS %DB_NAME%;"

echo 3. Creating %DB_NAME% database...
docker-compose -f %COMPOSE_FILE% exec -T postgres psql -U postgres -c "CREATE DATABASE %DB_NAME%;"

echo 4. Rebuilding live_core_service image...
docker-compose -f %COMPOSE_FILE% build --no-cache %SERVICE_NAME% celery_worker

echo 5. Starting services...
docker-compose -f %COMPOSE_FILE% up -d %SERVICE_NAME% celery_worker

echo 6. Waiting for services to start (5 seconds)...
timeout /t 5 /nobreak >nul

echo 7. Checking service status...
docker-compose -f %COMPOSE_FILE% ps %SERVICE_NAME% celery_worker

echo [OK] Rebuild complete!
echo Tip: Use 'docker-compose -f %COMPOSE_FILE% logs -f %SERVICE_NAME%' to view logs
echo Note: Other databases (media_download_test, users_service_test) are preserved.
