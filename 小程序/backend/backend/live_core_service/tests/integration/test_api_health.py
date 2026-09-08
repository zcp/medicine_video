"""
健康检查模块 API 层测试

测试 app.api.v1.endpoints.health 中的健康检查端点
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock


class TestHealthCheckAPI:
    """测试健康检查 API 端点"""
    
    @pytest.mark.asyncio
    async def test_api_health_check_success(self, async_client):
        """测试基础健康检查端点 - 成功"""
        # ===== Arrange (准备) =====
        # 使用 async_client fixture（复用现有 async_client fixture），无需认证
        
        # ===== Act (执行) =====
        # GET "/api/v1/health"（注意：路由prefix在 api/v1/api.py 中定义为 /api/v1）
        async for client in async_client:
            response = await client.get("/api/v1/health")
        
            # ===== Assert (断言) =====
            # 断言 response.status_code == 200 且 response.json()["code"] == 200
            assert response.status_code == 200, "基础健康检查应返回 200"
            json_response = response.json()
            assert json_response["code"] == 200, "业务状态码应为 200"
            
            # 断言 response.json()["data"]["status"] == "healthy"
            assert json_response["data"]["status"] == "healthy", "状态应为 healthy"
            
            # 断言 response.json()["data"]["service"] == "live-core-service"
            assert json_response["data"]["service"] == "live-core-service", "服务名称应正确"
            
            # 断言 response.json()["data"]["version"] 存在
            assert "version" in json_response["data"], "应包含版本号"
            
            # 断言 response.json()["data"]["timestamp"] 存在
            assert "timestamp" in json_response["data"], "应包含时间戳"
    
    @pytest.mark.asyncio
    async def test_api_readiness_check_success(self, async_client):
        """测试就绪检查端点 - 数据库连接正常"""
        # ===== Arrange (准备) =====
        # 使用 async_client fixture（复用现有 async_client fixture），确保数据库连接正常
        # async_client 已经通过依赖覆盖使用了测试数据库，无需额外的 db_session
        
        # ===== Act (执行) =====
        async for client in async_client:
            response = await client.get("/api/v1/health/ready")
        
            # ===== Assert (断言) =====
            # 断言 response.status_code == 200 且 response.json()["code"] == 200
            assert response.status_code == 200, "就绪检查应返回 200"
            json_response = response.json()
            assert json_response["code"] == 200, "业务状态码应为 200"
            
            # 断言 response.json()["data"]["status"] == "ready"
            assert json_response["data"]["status"] == "ready", "状态应为 ready"
            
            # 断言 response.json()["data"]["database"] == "connected"
            assert json_response["data"]["database"] == "connected", "数据库状态应为 connected"
            
            # 断言 response.json()["data"]["timestamp"] 存在
            assert "timestamp" in json_response["data"], "应包含时间戳"
    
    @pytest.mark.asyncio
    async def test_api_readiness_check_database_disconnected(self, async_client, mocker):
        """测试就绪检查端点 - 数据库连接失败"""
        # ===== Arrange (准备) =====
        # 使用 async_client fixture（复用现有 async_client fixture）
        # Mock app.crud.health.check_database_connection 返回 False（使用 mocker.patch("app.crud.health.check_database_connection", new_callable=AsyncMock, return_value=False)）
        mocker.patch(
            "app.crud.health.check_database_connection",
            new_callable=AsyncMock,
            return_value=False
        )
        
        # ===== Act (执行) =====
        async for client in async_client:
            response = await client.get("/api/v1/health/ready")
        
            # ===== Assert (断言) =====
            # 断言 response.status_code == 503
            assert response.status_code == 503, "数据库连接失败应返回 503"
            
            json_response = response.json()
            # 断言 response.json()["data"]["status"] == "not_ready"
            assert json_response["data"]["status"] == "not_ready", "状态应为 not_ready"
            
            # 断言 response.json()["data"]["database"] == "disconnected"
            assert json_response["data"]["database"] == "disconnected", "数据库状态应为 disconnected"
            
            # 断言 response.json()["data"]["error"] 存在
            assert "error" in json_response["data"], "应包含错误信息"
    
    @pytest.mark.asyncio
    async def test_api_config_check_success(self, async_client):
        """测试配置检查端点 - 成功"""
        # ===== Arrange (准备) =====
        # 使用 async_client fixture（复用现有 async_client fixture），无需认证
        
        # ===== Act (执行) =====
        async for client in async_client:
            response = await client.get("/api/v1/health/config")
        
            # ===== Assert (断言) =====
            # 断言 response.status_code == 200 且 response.json()["code"] == 200
            assert response.status_code == 200, "配置检查应返回 200"
            json_response = response.json()
            assert json_response["code"] == 200, "业务状态码应为 200"
            
            # 断言 response.json()["data"]["status"] == "configured"
            assert json_response["data"]["status"] == "configured", "状态应为 configured"
            
            # 断言 response.json()["data"]["config"] 存在
            assert "config" in json_response["data"], "应包含配置信息"
            
            # 断言 response.json()["data"]["config"]["environment"] 存在
            assert "environment" in json_response["data"]["config"], "应包含环境信息"
            
            # 断言 response.json()["data"]["config"]["database"] 存在
            assert "database" in json_response["data"]["config"], "应包含数据库配置"
            
            # 必须验证敏感信息已脱敏：断言 response.json()["data"]["config"] 中不包含 password、secret、jwt_secret_key 等敏感字段（或这些字段所在的嵌套字典已被过滤）
            config = json_response["data"]["config"]
            sensitive_keywords = ["password", "secret", "key", "token", "api_key", "jwt_secret_key", "database_password"]
            
            def check_no_sensitive_fields(obj):
                """递归检查对象中是否不包含敏感字段"""
                if isinstance(obj, dict):
                    for key in obj.keys():
                        # 如果键名包含敏感关键词，则失败
                        if any(sensitive in key.lower() for sensitive in sensitive_keywords):
                            pytest.fail(f"配置中包含敏感字段: {key}")
                        # 递归检查值
                        check_no_sensitive_fields(obj[key])
                elif isinstance(obj, (list, tuple)):
                    for item in obj:
                        check_no_sensitive_fields(item)
            
            # 验证配置中不包含敏感字段
            check_no_sensitive_fields(config)
            
            # 断言 response.json()["data"]["timestamp"] 存在
            assert "timestamp" in json_response["data"], "应包含时间戳"

