@echo off
REM Docker Compose rebuild script (Windows)

set COMPOSE_FILE=compose-app.windows.yml
set SERVICE_NAME=live_core_service

echo === Docker Compose Rebuild Script ===
echo.

if "%1"=="--full" goto full_rebuild
if "%1"=="-f" goto full_rebuild
if "%1"=="--code-only" goto code_rebuild
if "%1"=="-c" goto code_rebuild
goto usage

:full_rebuild
echo [WARN] Full rebuild mode (will delete database volume!)
set /p confirm="Continue? (y/N): "
if /i not "%confirm%"=="y" (
    echo Cancelled
    exit /b 1
)

echo 1. Stopping all services...
docker-compose -f %COMPOSE_FILE% down

echo 2. Removing PostgreSQL volume...
docker volume ls | findstr pgdata
if %errorlevel%==0 (
    for /f "tokens=2" %%v in ('docker-compose -f %COMPOSE_FILE% config --volumes ^| findstr pgdata') do (
        docker volume rm %%v 2>nul
    )
)

echo 3. Rebuilding service images...
docker-compose -f %COMPOSE_FILE% build --no-cache %SERVICE_NAME% celery_worker

echo 4. Starting all services...
docker-compose -f %COMPOSE_FILE% up -d

echo 5. Waiting for services to start (10 seconds)...
timeout /t 10 /nobreak >nul

echo 6. Checking service status...
docker-compose -f %COMPOSE_FILE% ps

echo [OK] Rebuild complete!
echo Tip: Use 'docker-compose -f %COMPOSE_FILE% logs -f' to view logs
goto end

:code_rebuild
echo Code rebuild mode (preserving database data)

echo 1. Stopping related services...
docker-compose -f %COMPOSE_FILE% stop %SERVICE_NAME% celery_worker

echo 2. Removing old containers...
docker-compose -f %COMPOSE_FILE% rm -f %SERVICE_NAME% celery_worker

echo 3. Rebuilding images...
docker-compose -f %COMPOSE_FILE% build --no-cache %SERVICE_NAME% celery_worker

echo 4. Starting services...
docker-compose -f %COMPOSE_FILE% up -d %SERVICE_NAME% celery_worker

echo 5. Checking service status...
docker-compose -f %COMPOSE_FILE% ps

echo [OK] Rebuild complete!
echo Tip: Use 'docker-compose -f %COMPOSE_FILE% logs -f %SERVICE_NAME%' to view logs
goto end

:usage
echo Usage:
echo   rebuild.bat --code-only or -c    # Rebuild code only (keep database)
echo   rebuild.bat --full or -f         # Full rebuild (delete database volume)
echo.
echo Examples:
echo   rebuild.bat -c                   # Use when code changes only
echo   rebuild.bat -f                   # Use when database schema changes

:end
