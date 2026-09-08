@echo off
REM Windows dev: docker compose -f docker-compose.yml -f docker-compose.windows.yml %*
docker compose -f docker-compose.yml -f docker-compose.windows.yml %*
