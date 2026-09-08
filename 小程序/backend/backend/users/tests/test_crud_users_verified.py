"""
用户CRUD单元测试 - 用户功能服务
对app/crud/crud_user.py中的每个函数进行详细的单元测试
"""

import pytest
import uuid
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import crud_user
from app.schemas.users import UserCreate
from app.models.users import User, UserRole, EntityStatus


class TestCrudUserCreate:
    """测试用户创建功能"""
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, db_session: AsyncSession):
        """
        测试成功创建用户
        - 创建UserCreate对象和密码哈希
        - 调用crud_user.create()
        - 验证返回的User对象字段值
        - 验证默认值设置正确
        """
        # 准备
        async for db in db_session:
            unique_id = uuid.uuid4().hex[:8]
            user_data = UserCreate(
                username=f"testuser_{unique_id}",
                email=f"test_{unique_id}@example.com",
                nickname="Test User",
                phone_number=None,
                social_provider=None,
                social_id=None
            )
            password_hash = "hashed_password_123"

            # 执行
            result = await crud_user.create(db, user_data, password_hash)

            # 断言数据库状态
            assert result is not None, "返回的User对象不应为None"
            assert result.username == user_data.username, "用户名应该匹配"
            assert result.email == user_data.email, "邮箱应该匹配"
            assert result.nickname == user_data.nickname, "昵称应该匹配"
            assert result.password_hash == password_hash, "密码哈希应该匹配"

            # 验证默认值
            assert result.role == UserRole.REGULAR, "默认角色应该是REGULAR"
            assert result.status == EntityStatus.NORMAL, "默认状态应该是NORMAL"
            assert result.is_email_verified is False, "邮箱验证状态应该是False"
            assert result.is_phone_verified is False, "手机验证状态应该是False"

            # 验证自动生成的字段
            assert result.id is not None, "ID应该被自动生成"
            assert result.public_id is not None, "public_id应该被自动生成"
            assert result.created_at is not None, "创建时间应该被自动设置"
            assert result.updated_at is not None, "更新时间应该被自动设置"

    @pytest.mark.asyncio
    async def test_create_user_fails_on_duplicate_username(self, db_session: AsyncSession):
        """
        测试重复用户名创建失败
        - 先创建一个用户
        - 尝试使用相同用户名再次创建
        - 验证抛出IntegrityError异常
        """
        # 准备
        async for db in db_session:
            unique_id = uuid.uuid4().hex[:8]
            username = f"duplicate_user_{unique_id}"
            user_data1 = UserCreate(
                username=username,
                email=f"first_{unique_id}@example.com",
                nickname="First User",
                phone_number=None,
                social_provider=None,
                social_id=None
            )
            user_data2 = UserCreate(
                username=username,  # 相同的用户名
                email=f"second_{unique_id}@example.com",
                nickname="Second User",
                phone_number=None,
                social_provider=None,
                social_id=None
            )
            password_hash = "hashed_password_123"

            # 执行 - 先成功创建第一个用户
            await crud_user.create(db, user_data1, password_hash)

            # 断言异常 - 尝试创建重复用户名应该失败
            with pytest.raises(IntegrityError):
                await crud_user.create(db, user_data2, password_hash)


class TestCrudUserGetByUsername:
    """测试根据用户名查询用户功能"""
    
    @pytest.mark.asyncio
    async def test_get_by_username_found(self, db_session: AsyncSession):
        """
        测试根据用户名成功查找用户
        - 先创建一个用户
        - 使用用户名查询
        - 验证返回正确的用户对象
        """
        # 准备 - 创建测试用户
        async for db in db_session:
            unique_id = uuid.uuid4().hex[:8]
            username = f"findme_user_{unique_id}"
            user_data = UserCreate(
                username=username,
                email=f"findme_{unique_id}@example.com",
                nickname="Find Me",
                phone_number=None,
                social_provider=None,
                social_id=None
            )
            created_user = await crud_user.create(db, user_data, "password_hash")

            # 执行
            result = await crud_user.get_by_username(db, username)

            # 断言
            assert result is not None, "应该找到用户"
            assert result.username == username, "用户名应该匹配"
            assert result.id == created_user.id, "用户ID应该匹配"
    
    @pytest.mark.asyncio
    async def test_get_by_username_not_found(self, db_session: AsyncSession):
        """
        测试根据不存在的用户名查询
        - 使用不存在的用户名查询
        - 验证返回None
        """
        # 执行
        async for db in db_session:
            result = await crud_user.get_by_username(db, "nonexistent_user")

            # 断言
            assert result is None, "不存在的用户名应该返回None"
    
    @pytest.mark.asyncio
    async def test_get_by_username_with_email_as_username(self, db_session: AsyncSession):
        """
        测试使用邮箱作为用户名查询
        - 创建一个用户
        - 使用邮箱地址作为用户名查询
        - 验证能够找到用户（因为get_by_username支持邮箱登录）
        """
        # 准备 - 创建测试用户
        async for db in db_session:
            unique_id = uuid.uuid4().hex[:8]
            email = f"email_login_{unique_id}@example.com"
            user_data = UserCreate(
                username=f"email_login_user_{unique_id}",
                email=email,
                nickname="Email Login User",
                phone_number=None,
                social_provider=None,
                social_id=None
            )
            created_user = await crud_user.create(db, user_data, "password_hash")

            # 执行 - 使用邮箱作为用户名查询
            result = await crud_user.get_by_username(db, email)

            # 断言
            assert result is not None, "使用邮箱作为用户名应该能找到用户"
            assert result.email == email, "邮箱应该匹配"
            assert result.id == created_user.id, "用户ID应该匹配"


class TestCrudUserGetByEmail:
    """测试根据邮箱查询用户功能"""
    
    @pytest.mark.asyncio
    async def test_get_by_email_found(self, db_session: AsyncSession):
        """
        测试根据邮箱成功查找用户
        - 先创建一个用户
        - 使用邮箱查询
        - 验证返回正确的用户对象
        """
        # 准备 - 创建测试用户
        async for db in db_session:
            unique_id = uuid.uuid4().hex[:8]
            email = f"email_test_{unique_id}@example.com"
            user_data = UserCreate(
                username=f"email_test_user_{unique_id}",
                email=email,
                nickname="Email Test User",
                phone_number=None,
                social_provider=None,
                social_id=None
            )
            created_user = await crud_user.create(db, user_data, "password_hash")

            # 执行
            result = await crud_user.get_by_email(db, email)

            # 断言
            assert result is not None, "应该找到用户"
            assert result.email == email, "邮箱应该匹配"
            assert result.id == created_user.id, "用户ID应该匹配"
    
    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, db_session: AsyncSession):
        """
        测试根据不存在的邮箱查询
        - 使用不存在的邮箱查询
        - 验证返回None
        """
        # 执行
        async for db in db_session:
            result = await crud_user.get_by_email(db, "nonexistent@example.com")

            # 断言
            assert result is None, "不存在的邮箱应该返回None"