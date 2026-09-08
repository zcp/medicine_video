"""
健康检查模块 CRUD 层测试

测试 app.crud.health 中的数据库连接测试功能
"""
import pytest
from app.crud import health as crud_health
from unittest.mock import patch


class TestCheckDatabaseConnection:
    """测试数据库连接检查函数"""
    
    @pytest.mark.asyncio
    async def test_check_database_connection_success(self, db_session):
        """测试数据库连接成功"""
        async for db in db_session:
            # ===== Arrange (准备) =====
            # 使用 db_session fixture（复用现有 db_session fixture），确保数据库连接正常
            
            # ===== Act (执行) =====
            result = await crud_health.check_database_connection(db)
            
            # ===== Assert (断言) =====
            assert result is True, "数据库连接正常时应返回 True"
    
    @pytest.mark.asyncio
    async def test_check_database_connection_failure(self, db_session):
        """测试数据库连接失败"""
        async for db in db_session:
            # ===== Arrange (准备) =====
            # Mock db.execute 抛出异常来模拟数据库连接失败
            with patch.object(
                db, 
                'execute', 
                side_effect=Exception("Connection failed")
            ):
                
                # ===== Act (执行) =====
                result = await crud_health.check_database_connection(db)
                
                # ===== Assert (断言) =====
                assert result is False, "数据库连接失败时应返回 False"

