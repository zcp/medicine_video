"""
LiveCore Service - Topic Search Feature Incremental Tests (Service Layer)

This module contains incremental tests for the new search functionality
(title and topic_id filters) added to the topic list Service methods.
"""

import uuid
import pytest
from typing import List, Tuple
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

# 项目内导入（从实际代码中读取）
from app.services.topic_service import TopicService
from app.models.topic import TopicStatus


# ==================== Service层查询功能测试 ====================

@pytest.mark.asyncio
async def test_get_topic_list_with_title_parameter_passing(db_session):
    """
    测试Service层正确传递title参数到CRUD层
    
    验证点:
    1. CRUD层的get_multi_and_total被调用
    2. title参数值为传递的值
    3. 其他参数（page、size、role、current_user_id）也正确传递
    """
    async for db in db_session:
        # Arrange: Mock CRUD层的get_multi_and_total方法
        mock_topics = []
        mock_total = 0
        
        with patch('app.crud.topic.get_multi_and_total', new_callable=AsyncMock) as mock_get_multi:
            mock_get_multi.return_value = (mock_topics, mock_total)
            
            service = TopicService(db)
            test_title = "test_search_keyword"
            test_user_id = uuid.uuid4()
            test_role = "REGULAR"
            
            # Act: 调用Service层方法
            await service.get_topic_list(
                page=1,
                size=10,
                title=test_title,
                role=test_role,
                current_user_id=test_user_id
            )
            
            # Assert: 验证CRUD层方法被调用，且参数正确
            assert mock_get_multi.called, "CRUD层的get_multi_and_total方法应该被调用"
            
            # 获取调用参数
            call_args = mock_get_multi.call_args
            assert call_args is not None, "调用参数不应为None"
            
            # 验证位置参数（只有db是位置参数）
            assert len(call_args[0]) == 1, f"期望1个位置参数（db），实际 {len(call_args[0])} 个"
            assert call_args[0][0] == db, "第一个位置参数应该是db"
            
            # 验证关键字参数
            kwargs = call_args[1] if len(call_args) > 1 else {}
            assert kwargs.get('skip') == 0, f"skip参数应该为0（page=1, size=10），实际为 {kwargs.get('skip')}"
            assert kwargs.get('limit') == 10, f"limit参数应该为10，实际为 {kwargs.get('limit')}"
            assert kwargs.get('title') == test_title, \
                f"title参数应该为 {test_title}，实际为 {kwargs.get('title')}"
            assert kwargs.get('current_user_id') == test_user_id, \
                f"current_user_id参数应该为 {test_user_id}，实际为 {kwargs.get('current_user_id')}"
            assert kwargs.get('current_user_role') == test_role, \
                f"current_user_role参数应该为 {test_role}，实际为 {kwargs.get('current_user_role')}"


@pytest.mark.asyncio
async def test_get_topic_list_with_topic_id_parameter_passing(db_session):
    """
    测试Service层正确传递topic_id参数到CRUD层
    
    验证点:
    1. CRUD层的get_multi_and_total被调用
    2. topic_id参数值为指定的UUID
    3. topic_id参数类型为uuid.UUID
    """
    async for db in db_session:
        # Arrange: Mock CRUD层的get_multi_and_total方法
        mock_topics = []
        mock_total = 0
        specific_topic_id = uuid.uuid4()
        
        with patch('app.crud.topic.get_multi_and_total', new_callable=AsyncMock) as mock_get_multi:
            mock_get_multi.return_value = (mock_topics, mock_total)
            
            service = TopicService(db)
            
            # Act: 调用Service层方法，传递topic_id参数
            await service.get_topic_list(
                page=1,
                size=10,
                topic_id=specific_topic_id,
                role=None,
                current_user_id=None
            )
            
            # Assert: 验证CRUD层方法被调用，且topic_id参数正确
            assert mock_get_multi.called, "CRUD层的get_multi_and_total方法应该被调用"
            
            # 获取调用参数
            call_args = mock_get_multi.call_args
            assert call_args is not None, "调用参数不应为None"
            
            # 验证关键字参数
            kwargs = call_args[1] if len(call_args) > 1 else {}
            assert kwargs.get('topic_id') == specific_topic_id, \
                f"topic_id参数应该为 {specific_topic_id}，实际为 {kwargs.get('topic_id')}"
            assert isinstance(kwargs.get('topic_id'), uuid.UUID), \
                f"topic_id参数类型应该为uuid.UUID，实际为 {type(kwargs.get('topic_id'))}"

