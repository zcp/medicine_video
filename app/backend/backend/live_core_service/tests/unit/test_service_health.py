"""
健康检查模块 Service 层测试

测试 app.services.health_service.HealthService 的业务逻辑
"""
import pytest
from unittest.mock import AsyncMock

from app.services.health_service import HealthService


class TestHealthService:
    """测试 HealthService 类"""
    
    @pytest.mark.asyncio
    async def test_check_readiness_success(self, mocker):
        """测试检查就绪状态 - 数据库连接正常"""
        # ===== Arrange (准备) =====
        # Mock app.crud.health.check_database_connection (使用 new_callable=AsyncMock) 并使其返回 True
        mock_check = mocker.patch(
            "app.crud.health.check_database_connection",
            new_callable=AsyncMock,
            return_value=True
        )
        
        # 创建 HealthService 实例
        health_service = HealthService()
        
        # 创建一个模拟的数据库会话用于传递
        db = AsyncMock()
        
        # ===== Act (执行) =====
        result = await health_service.check_readiness(db)
        
        # ===== Assert (断言) =====
        # 必须断言 crud_health.check_database_connection 被正确调用
        # 注意：Service层调用时使用位置参数，所以断言也要使用位置参数
        mock_check.assert_called_once_with(db)
        
        # 断言返回的字典包含 {"status": "ready", "database": "connected", "error": None}
        assert result == {
            "status": "ready",
            "database": "connected",
            "error": None
        }, "数据库连接正常时应返回就绪状态"
    
    @pytest.mark.asyncio
    async def test_check_readiness_database_disconnected(self, mocker):
        """测试检查就绪状态 - 数据库连接失败"""
        # ===== Arrange (准备) =====
        # Mock app.crud.health.check_database_connection (使用 new_callable=AsyncMock) 并使其返回 False
        mock_check = mocker.patch(
            "app.crud.health.check_database_connection",
            new_callable=AsyncMock,
            return_value=False
        )
        
        # 创建 HealthService 实例
        health_service = HealthService()
        
        # 创建一个模拟的数据库会话用于传递
        db = AsyncMock()
        
        # ===== Act (执行) =====
        result = await health_service.check_readiness(db)
        
        # ===== Assert (断言) =====
        # 必须断言 crud_health.check_database_connection 被正确调用
        # 注意：Service层调用时使用位置参数，所以断言也要使用位置参数
        mock_check.assert_called_once_with(db)
        
        # 断言返回的字典包含 {"status": "not_ready", "database": "disconnected", "error": "连接数据库失败"}
        assert result == {
            "status": "not_ready",
            "database": "disconnected",
            "error": "连接数据库失败"
        }, "数据库连接失败时应返回未就绪状态"

