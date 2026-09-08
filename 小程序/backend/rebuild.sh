#!/bin/bash
# Docker Compose 快速重建脚本

set -e

COMPOSE_FILE="docker-compose.yml"
SERVICE_NAME="live_core_service"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Docker Compose 重建脚本 ===${NC}"
echo ""

# 检查参数
if [ "$1" == "--full" ] || [ "$1" == "-f" ]; then
    echo -e "${YELLOW}⚠️  完整重建模式（会删除数据库 volume，数据将丢失！）${NC}"
    read -p "确认继续？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消"
        exit 1
    fi
    
    echo -e "${GREEN}1. 停止所有服务...${NC}"
    docker-compose -f $COMPOSE_FILE down
    
    echo -e "${GREEN}2. 删除 PostgreSQL volume...${NC}"
    VOLUME_NAME=$(docker-compose -f $COMPOSE_FILE config --volumes | grep pgdata | head -1)
    if [ -n "$VOLUME_NAME" ]; then
        docker volume rm ${VOLUME_NAME} 2>/dev/null || echo "Volume 不存在或已被删除"
    else
        # 尝试常见的 volume 名称
        docker volume rm live-streaming-saas_pgdata compose-app_pgdata 2>/dev/null || echo "Volume 不存在或已被删除"
    fi
    
    echo -e "${GREEN}3. 重新构建服务镜像...${NC}"
    docker-compose -f $COMPOSE_FILE build --no-cache $SERVICE_NAME celery_worker
    
    echo -e "${GREEN}4. 启动所有服务...${NC}"
    docker-compose -f $COMPOSE_FILE up -d
    
    echo -e "${GREEN}5. 等待服务启动（10秒）...${NC}"
    sleep 10
    
    echo -e "${GREEN}6. 查看服务状态...${NC}"
    docker-compose -f $COMPOSE_FILE ps
    
    echo -e "${GREEN}✅ 重建完成！${NC}"
    echo -e "${YELLOW}提示：使用 'docker-compose -f $COMPOSE_FILE logs -f' 查看日志${NC}"
    
elif [ "$1" == "--code-only" ] || [ "$1" == "-c" ]; then
    echo -e "${GREEN}代码重建模式（保留数据库数据）${NC}"
    
    echo -e "${GREEN}1. 停止相关服务...${NC}"
    docker-compose -f $COMPOSE_FILE stop $SERVICE_NAME celery_worker
    
    echo -e "${GREEN}2. 删除旧容器...${NC}"
    docker-compose -f $COMPOSE_FILE rm -f $SERVICE_NAME celery_worker
    
    echo -e "${GREEN}3. 重新构建镜像...${NC}"
    docker-compose -f $COMPOSE_FILE build --no-cache $SERVICE_NAME celery_worker
    
    echo -e "${GREEN}4. 启动服务...${NC}"
    docker-compose -f $COMPOSE_FILE up -d $SERVICE_NAME celery_worker
    
    echo -e "${GREEN}5. 查看服务状态...${NC}"
    docker-compose -f $COMPOSE_FILE ps
    
    echo -e "${GREEN}✅ 重建完成！${NC}"
    echo -e "${YELLOW}提示：使用 'docker-compose -f $COMPOSE_FILE logs -f $SERVICE_NAME' 查看日志${NC}"
    
else
    echo "用法："
    echo "  ./rebuild.sh --code-only 或 -c    # 仅重建代码（保留数据库）"
    echo "  ./rebuild.sh --full 或 -f         # 完整重建（删除数据库 volume）"
    echo ""
    echo "示例："
    echo "  ./rebuild.sh -c                   # 仅修改代码时使用"
    echo "  ./rebuild.sh -f                   # 修改数据库结构时使用（开发/测试）"
fi


