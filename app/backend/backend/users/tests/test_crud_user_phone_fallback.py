"""
CRUD 手机号归一化兜底查询单元测试 - test_crud_user_phone_fallback.py
覆盖 crud_user.py 的 get_by_phone_number / get_by_login_identifier 兜底逻辑（阶段 D 出口审查验收项）
纯 mock 风格，不依赖真实数据库连接。
"""
from unittest.mock import MagicMock

import pytest
from sqlalchemy.dialects import postgresql

from app.crud import crud_user


class FakeResult:
    """模拟 db.execute 的返回值，按序返回预设结果"""

    def __init__(self, user):
        self._user = user

    def scalar_one_or_none(self):
        return self._user


class FakeDb:
    """记录所有 execute 调用并捕获传入的 SQLAlchemy 语句"""

    def __init__(self, *results):
        self._results = list(results)
        self.executed = []

    async def execute(self, stmt):
        self.executed.append(stmt)
        result = self._results.pop(0)
        return FakeResult(result)


def _compile(stmt) -> str:
    """将语句编译为内联参数值的 SQL 字符串，便于断言查询条件"""
    return str(
        stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
    )


class TestGetByPhoneNumber:
    """测试 get_by_phone_number 兜底查询"""

    @pytest.mark.asyncio
    async def test_exact_match_single_query(self):
        """精确匹配命中：只执行一次查询"""
        user = MagicMock()
        db = FakeDb(user)
        result = await crud_user.get_by_phone_number(db, phone_number="+8613800138000")
        assert result is user
        assert len(db.executed) == 1

    @pytest.mark.asyncio
    async def test_pure_11_fallback_finds_dirty_plus86_in_db(self):
        """关键场景：库中存 +86 脏格式，纯 11 位入参经候选集兜底命中"""
        user = MagicMock()
        db = FakeDb(None, user)
        result = await crud_user.get_by_phone_number(db, phone_number="13800138000")
        assert result is user
        assert len(db.executed) == 2
        sql = _compile(db.executed[1])
        assert "8613800138000" in sql
        assert "+8613800138000" in sql

    @pytest.mark.asyncio
    async def test_plus86_input_fallback_query(self):
        """+86 前缀入参精确未命中：候选集兜底查询命中"""
        user = MagicMock()
        db = FakeDb(None, user)
        result = await crud_user.get_by_phone_number(db, phone_number="+8613800138000")
        assert result is user
        assert len(db.executed) == 2
        sql = _compile(db.executed[1])
        assert "13800138000" in sql
        assert "8613800138000" in sql

    @pytest.mark.asyncio
    async def test_both_miss_returns_none(self):
        """精确与兜底均未命中：返回 None，执行两次查询"""
        db = FakeDb(None, None)
        result = await crud_user.get_by_phone_number(db, phone_number="+8613800138000")
        assert result is None
        assert len(db.executed) == 2

    @pytest.mark.asyncio
    async def test_non_phone_no_fallback(self):
        """非手机号入参（归一化抛 ValueError）：不触发兜底查询"""
        db = FakeDb(None)
        result = await crud_user.get_by_phone_number(db, phone_number="not-a-phone")
        assert result is None
        assert len(db.executed) == 1


class TestGetByLoginIdentifier:
    """测试 get_by_login_identifier 手机号分支兜底查询"""

    @pytest.mark.asyncio
    async def test_phone_exact_match_single_query(self):
        """手机号精确匹配命中：只执行一次查询"""
        user = MagicMock()
        db = FakeDb(user)
        result = await crud_user.get_by_login_identifier(db, identifier="13800138000")
        assert result is user
        assert len(db.executed) == 1

    @pytest.mark.asyncio
    async def test_pure_11_fallback_finds_dirty_plus86_in_db(self):
        """关键场景：库中存 +86 脏格式，纯 11 位登录标识符经候选集兜底命中"""
        user = MagicMock()
        db = FakeDb(None, user)
        result = await crud_user.get_by_login_identifier(db, identifier="13800138000")
        assert result is user
        assert len(db.executed) == 2
        sql = _compile(db.executed[1])
        assert "8613800138000" in sql
        assert "is_phone_verified" in sql

    @pytest.mark.asyncio
    async def test_13_digits_identifier_fallback(self):
        """86 前缀 13 位标识符精确未命中：候选集兜底查询命中"""
        user = MagicMock()
        db = FakeDb(None, user)
        result = await crud_user.get_by_login_identifier(db, identifier="8613800138000")
        assert result is user
        assert len(db.executed) == 2
        assert "13800138000" in _compile(db.executed[1])

    @pytest.mark.asyncio
    async def test_username_no_fallback(self):
        """用户名标识符：归一化抛 ValueError，不触发兜底查询"""
        db = FakeDb(None)
        result = await crud_user.get_by_login_identifier(db, identifier="alice")
        assert result is None
        assert len(db.executed) == 1

    @pytest.mark.asyncio
    async def test_email_no_fallback(self):
        """邮箱标识符：归一化抛 ValueError，不触发兜底查询"""
        db = FakeDb(None)
        result = await crud_user.get_by_login_identifier(db, identifier="a@b.com")
        assert result is None
        assert len(db.executed) == 1
