#!/bin/bash
# 危险：DROP live_core_test（清房间数据）；不清 users 账号
# 日常发版请用 ./rebuild-live-core-only.sh

set -e

COMPOSE_FILE="docker-compose.yml"
SERVICE_NAME="live_core_service"
DB_NAME="live_core_test"

echo "=== RESET $DB_NAME (users DB kept) ==="
read -p "Type YES to continue: " CONFIRM
if [[ "$CONFIRM" != "YES" ]]; then
  echo "Cancelled."
  exit 0
fi

docker compose -f "$COMPOSE_FILE" stop "$SERVICE_NAME" celery_worker
docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U postgres -c "CREATE DATABASE $DB_NAME;"
docker compose -f "$COMPOSE_FILE" build "$SERVICE_NAME" celery_worker
docker compose -f "$COMPOSE_FILE" up -d "$SERVICE_NAME" celery_worker
echo "✅ Done. users_service_test untouched."
