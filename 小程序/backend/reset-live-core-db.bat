@echo off
setlocal

REM 危险：DROP live_core_test 并重建（会清房间等直播核心数据）
REM 不会动 users_service_test，账号仍保留
REM 日常发版请用 rebuild-live-core-only.bat

set COMPOSE=compose -f docker-compose.yml -f docker-compose.windows.yml
set SERVICE_NAME=live_core_service
set DB_NAME=live_core_test

echo ========================================
echo   RESET Live Core DATABASE
echo   Drops %DB_NAME% only (users DB kept)
echo ========================================
set /p CONFIRM=Type YES to continue: 
if /I not "%CONFIRM%"=="YES" (
  echo Cancelled.
  exit /b 0
)

docker %COMPOSE% stop %SERVICE_NAME% celery_worker
docker %COMPOSE% exec -T postgres psql -U postgres -c "DROP DATABASE IF EXISTS %DB_NAME%;"
docker %COMPOSE% exec -T postgres psql -U postgres -c "CREATE DATABASE %DB_NAME%;"
docker %COMPOSE% build %SERVICE_NAME% celery_worker
docker %COMPOSE% up -d %SERVICE_NAME% celery_worker
docker %COMPOSE% ps %SERVICE_NAME% celery_worker
echo Done. users_service_test untouched.
