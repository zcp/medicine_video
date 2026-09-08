#!/bin/bash
# 仅重建 live_core_service 数据库（保留其他数据库数据）

set -e

COMPOSE_FILE="compose-app.yml"
SERVICE_NAME="live_core_service"
DB_NAME="live_core_test"

echo "=== 仅重建 live_core_service 数据库 ==="
echo "⚠️  这将删除 $DB_NAME 数据库，但保留其他数据库（media_download_test, users_service_test）的数据"
echo ""
read -p "确认继续？(y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 1
fi

echo "1. 停止 live_core_service 和 celery_worker..."
docker-compose -f $COMPOSE_FILE stop $SERVICE_NAME celery_worker

echo "2. 删除 $DB_NAME 数据库..."
docker-compose -f $COMPOSE_FILE exec -T postgres psql -U postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"

echo "3. 重新创建 $DB_NAME 数据库..."
docker-compose -f $COMPOSE_FILE exec -T postgres psql -U postgres -c "CREATE DATABASE $DB_NAME;"

echo "4. 重新构建 live_core_service 镜像..."
docker-compose -f $COMPOSE_FILE build --no-cache $SERVICE_NAME celery_worker

echo "5. 启动服务..."
docker-compose -f $COMPOSE_FILE up -d $SERVICE_NAME celery_worker

echo "6. 等待服务启动（5秒）..."
sleep 5

echo "7. 查看服务状态..."
docker-compose -f $COMPOSE_FILE ps $SERVICE_NAME celery_worker

echo "✅ 重建完成！"
echo "提示：使用 'docker-compose -f $COMPOSE_FILE logs -f $SERVICE_NAME' 查看日志"
echo "注意：其他数据库（media_download_test, users_service_test）的数据已保留"


