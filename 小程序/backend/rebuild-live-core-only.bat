@echo off
setlocal

REM 仅重建 live_core 镜像并重启服务 —— 不 DROP 任何数据库，不清除账号
REM 用法: rebuild-live-core-only.bat
REM 若需重置 live_core 库（会清房间数据，不清 users 账号），请用: reset-live-core-db.bat

set COMPOSE=compose -f docker-compose.yml -f docker-compose.windows.yml
set SERVICE_NAME=live_core_service

echo ========================================
echo   Rebuild Live Core Service ONLY
echo   (NO database drop, accounts kept)
echo ========================================

docker %COMPOSE% build %SERVICE_NAME% celery_worker
if errorlevel 1 (
  echo Build failed.
  exit /b 1
)

docker %COMPOSE% up -d --no-deps %SERVICE_NAME% celery_worker
if errorlevel 1 (
  echo Up failed.
  exit /b 1
)

docker %COMPOSE% ps %SERVICE_NAME% celery_worker
echo.
echo Done. Postgres volumes untouched; user accounts preserved.
