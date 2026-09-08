@echo off
chcp 65001 >nul
echo Stopping dev environment...
docker compose -f docker-compose.yml -f docker-compose.windows.yml down
echo Done.
