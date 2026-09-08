@echo off
chcp 65001 >nul
echo ========================================
echo   Windows Docker Dev Environment Stop
echo ========================================
echo.

echo Stopping all services...
docker-compose -f compose-app.windows.yml down

if %errorlevel% neq 0 (
    echo [FAIL] Error stopping services
    pause
    exit /b 1
)

echo.
echo ========================================
echo   [OK] All services stopped
echo ========================================
echo.
echo Note: Data is saved in Docker volumes and will be restored on next start.
echo.
pause
