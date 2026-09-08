#!/bin/bash
# 仅重建 live_core_service 镜像并重启 —— 不 DROP 任何数据库，不清除账号
# 用法: ./rebuild-live-core-only.sh
# 若需重置 live_core 库，请用: ./reset-live-core-db.sh

set -e

COMPOSE_FILE="docker-compose.yml"
SERVICE_NAME="live_core_service"

echo "=== Rebuild Live Core Service ONLY (no DB drop) ==="

docker compose -f "$COMPOSE_FILE" build "$SERVICE_NAME" celery_worker
docker compose -f "$COMPOSE_FILE" up -d --no-deps "$SERVICE_NAME" celery_worker
docker compose -f "$COMPOSE_FILE" ps "$SERVICE_NAME" celery_worker

echo "✅ 完成。未删除任何数据库；users 账号保留。"
