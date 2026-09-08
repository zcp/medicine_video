@echo off
chcp 65001 >nul
echo ========================================
echo   Windows Docker Dev Environment Launcher
echo ========================================
echo.

REM Check Docker status
echo [1/5] Checking Docker status...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] Docker is not running!
    echo        Please start Docker Desktop first.
    pause
    exit /b 1
)
echo [OK] Docker is running

REM Create necessary directories
echo.
echo [2/5] Creating necessary directories...
if not exist "data\live_core_media\rooms" (
    mkdir "data\live_core_media\rooms"
    echo [OK] Created data\live_core_media\rooms
)
if not exist "data\live_core_media\topics" (
    mkdir "data\live_core_media\topics"
    echo [OK] Created data\live_core_media\topics
)
if not exist "data\srs" (
    mkdir "data\srs"
    echo [OK] Created data\srs
)
if not exist "logs\srs" (
    mkdir "logs\srs"
    echo [OK] Created logs\srs
)
echo [OK] Directory check complete

REM Check port usage
echo.
echo [3/5] Checking port usage...
netstat -an | findstr ":8000" >nul
if %errorlevel%==0 (
    echo [WARN] Port 8000 is already in use
)
netstat -an | findstr ":8080" >nul
if %errorlevel%==0 (
    echo [WARN] Port 8080 is already in use
)
netstat -an | findstr ":5433" >nul
if %errorlevel%==0 (
    echo [WARN] Port 5433 is already in use
)

REM Start services
echo.
echo [4/5] Starting Docker services...
docker-compose -f compose-app.windows.yml up -d
if %errorlevel% neq 0 (
    echo [FAIL] Failed to start services!
    pause
    exit /b 1
)

REM Wait for services to start
echo.
echo [5/5] Waiting for services to start (10 seconds)...
timeout /t 10 /nobreak >nul

REM Show service status
echo.
echo ========================================
echo   Service Status
echo ========================================
docker-compose -f compose-app.windows.yml ps

echo.
echo ========================================
echo   [OK] Dev environment started!
echo ========================================
echo.
echo Access URLs:
echo    - Live Core API:       http://localhost:8000
echo    - Media Download API:  http://localhost:8001
echo    - User Service API:    http://localhost:8002
echo    - Nginx (Proxy):       http://localhost:8080
echo    - SRS Console:         http://localhost:8080/srs
echo.
echo Common Commands:
echo    - View logs:   docker-compose -f compose-app.windows.yml logs -f
echo    - Stop:        stop-dev.bat
echo    - Rebuild:     rebuild.bat -c
echo.
pause
