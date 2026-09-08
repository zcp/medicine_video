@echo off
chcp 65001 >nul
setlocal

set COMPOSE=compose -f docker-compose.yml -f docker-compose.windows.yml

echo ========================================
echo   Live Streaming SaaS - Dev (Windows)
echo   compose: docker-compose.yml + docker-compose.windows.yml
echo ========================================
echo.

echo [1/5] Checking Docker...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running. Start Docker Desktop first.
    pause
    exit /b 1
)
echo OK: Docker is running

echo.
echo [2/5] Creating data directories...
if not exist "data\live_core_media\rooms" mkdir "data\live_core_media\rooms"
if not exist "data\live_core_media\topics" mkdir "data\live_core_media\topics"
if not exist "data\srs" mkdir "data\srs"
if not exist "logs\srs" mkdir "logs\srs"
echo OK: directories ready

echo.
echo [3/5] Checking ports (8000, 8080, 5433)...
netstat -an | findstr ":8000" >nul && echo WARN: port 8000 in use
netstat -an | findstr ":8080" >nul && echo WARN: port 8080 in use
netstat -an | findstr ":5433" >nul && echo WARN: port 5433 in use

echo.
echo [4/5] Starting services...
docker %COMPOSE% up -d
if %errorlevel% neq 0 (
    echo ERROR: docker compose up failed
    pause
    exit /b 1
)

echo.
echo [5/5] Waiting for startup (10s)...
timeout /t 10 /nobreak >nul

echo.
echo ========================================
echo   Service Status
echo ========================================
docker %COMPOSE% ps

echo.
echo ========================================
echo   Dev environment is ready
echo ========================================
echo.
echo URLs:
echo   Live Core API:      http://localhost:8000
echo   Media Download API: http://localhost:8001
echo   User Service API:   http://localhost:8002
echo   Nginx proxy:        http://localhost:8080
echo   SRS console:        http://localhost:8080/srs
echo.
echo Commands:
echo   Logs:  docker %COMPOSE% logs -f
echo   Stop:  stop-dev.bat
echo   Test:  docker %COMPOSE% exec live_core_service pytest tests/ -q
echo.
pause
