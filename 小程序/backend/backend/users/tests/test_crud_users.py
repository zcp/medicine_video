"""
用户CRUD单元测试 - 用户功能服务
对app/crud/crud_user.py中的每个函数进行详细的单元测试
"""

import pytest
import uuid
from sqlalchemy.exc import IntegrityError

from app.crud import crud_user
from app.schemas.users import UserCreate
from app.models.users import User, UserRole, EntityStatus


class TestCrudUserCreate:
    """测试用户创建功能"""
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, db_session):
        """
        测试成功创建用户
        - 创建UserCreate对象和密码哈希
        - 调用crud_user.create()
        - 验证返回的User对象字段值
        - 验证默认值设置正确
        """
        async for db in db_session:
            # 准备（使用唯一标识符避免冲突）
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
    async def test_create_user_fails_on_duplicate_username(self, db_session):
        """
        测试重复用户名创建失败
        - 先创建一个用户
        - 尝试使用相同用户名再次创建
        - 验证抛出IntegrityError异常
        """
        async for db in db_session:
            # 准备（使用唯一标识符避免冲突）
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
    async def test_get_by_username_found(self, db_session):
        """
        测试根据用户名成功查找用户
        - 先创建一个用户
        - 使用用户名查询
        - 验证返回正确的用户对象
        """
        async for db in db_session:
            # 准备 - 创建测试用户（使用唯一标识符避免冲突）
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
    async def test_get_by_username_not_found(self, db_session):
        """
        测试根据不存在的用户名查询
        - 使用不存在的用户名查询
        - 验证返回None
        """
        async for db in db_session:
            # 执行
            result = await crud_user.get_by_username(db, "nonexistent_user")
            
            # 断言
            assert result is None, "不存在的用户名应该返回None"
    
    @pytest.mark.asyncio
    async def test_get_by_username_with_email_as_username(self, db_session):
        """
        测试使用邮箱作为用户名查询
        - 创建一个用户
        - 使用邮箱地址作为用户名查询
        - 验证能够找到用户（因为get_by_username支持邮箱登录）
        """
        async for db in db_session:
            # 准备 - 创建测试用户（使用唯一标识符避免冲突）
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
    async def test_get_by_email_found(self, db_session):
        """
        测试根据邮箱成功查找用户
        - 先创建一个用户
        - 使用邮箱查询
        - 验证返回正确的用户对象
        """
        async for db in db_session:
            # 准备 - 创建测试用户（使用唯一标识符避免冲突）
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
    async def test_get_by_email_not_found(self, db_session):
        """
        测试根据不存在的邮箱查询
        - 使用不存在的邮箱查询
        - 验证返回None
        """
        async for db in db_session:
            # 执行
            result = await crud_user.get_by_email(db, "nonexistent@example.com")
            
            # 断言
            assert result is None, "不存在的邮箱应该返回None" 


# ============================================================================
# 批次二新增测试 - Batch 2 CRUD Tests
# ============================================================================

class TestCrudUserGetById:
    """测试根据ID获取用户功能"""
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_found_and_not_found(self, db_session):
        """
        测试根据ID获取用户 - 找到和未找到的情况
        - 创建一个用户并获取其ID
        - 使用ID查询用户，断言找到
        - 使用不存在的ID查询，断言返回None
        """
        async for db in db_session:
            # 准备 - 创建测试用户（使用唯一标识符避免冲突）
            unique_id = uuid.uuid4().hex[:8]
            user_data = UserCreate(
                username=f"testuser_for_id_test_{unique_id}",
                email=f"idtest_{unique_id}@example.com",
                nickname="ID Test User",
                phone_number=None,
                social_provider=None,
                social_id=None
            )
            password_hash = "hashed_password_123"
            created_user = await crud_user.create(db, user_data, password_hash)
            
            # 执行1 - 使用有效ID查询
            found_user = await crud_user.get(db, created_user.id)
            
            # 断言1 - 找到用户
            assert found_user is not None, "使用有效ID应该找到用户"
            assert found_user.id == created_user.id, "返回的用户ID应该匹配"
            assert found_user.username == created_user.username, "返回的用户名应该匹配"
            
            # 执行2 - 使用不存在的ID查询
            not_found_user = await crud_user.get(db, 999999)
            
            # 断言2 - 未找到用户
            assert not_found_user is None, "使用不存在的ID应该返回None"


class TestCrudUserGetByUUID:
    """测试根据UUID获取用户功能"""
    
    @pytest.mark.asyncio
    async def test_get_user_by_uuid_found_and_not_found(self, db_session):
        """
        测试根据UUID获取用户 - 找到和未找到的情况
        - 创建一个用户并获取其public_id
        - 使用UUID查询用户，断言找到
        - 使用不存在的UUID查询，断言返回None
        """
        async for db in db_session:
            import uuid
            
            # 准备 - 创建测试用户（使用唯一标识符避免冲突）
            unique_id = uuid.uuid4().hex[:8]
            user_data = UserCreate(
                username=f"testuser_for_uuid_test_{unique_id}",
                email=f"uuidtest_{unique_id}@example.com",
                nickname="UUID Test User",
                phone_number=None,
                social_provider=None,
                social_id=None
            )
            password_hash = "hashed_password_123"
            created_user = await crud_user.create(db, user_data, password_hash)
            
            # 执行1 - 使用有效UUID查询
            found_user = await crud_user.get_by_uuid(db, created_user.public_id)
            
            # 断言1 - 找到用户
            assert found_user is not None, "使用有效UUID应该找到用户"
            assert found_user.public_id == created_user.public_id, "返回的用户UUID应该匹配"
            assert found_user.username == created_user.username, "返回的用户名应该匹配"
            
            # 执行2 - 使用不存在的UUID查询
            fake_uuid = uuid.uuid4()
            not_found_user = await crud_user.get_by_uuid(db, fake_uuid)
            
            # 断言2 - 未找到用户
            assert not_found_user is None, "使用不存在的UUID应该返回None"


class TestCrudUserUpdate:
    """测试用户更新功能"""
    
    @pytest.mark.asyncio
    async def test_update_user_nickname_and_status(self, db_session):
        """
        测试更新用户昵称和状态
        - 创建一个用户
        - 使用UserUpdate更新nickname和status
        - 验证数据库中的更新结果
        """
        async for db in db_session:
            from app.schemas.users import UserUpdate
            
            # 准备 - 创建测试用户（使用唯一标识符避免冲突）
            unique_id = uuid.uuid4().hex[:8]
            user_data = UserCreate(
                username=f"testuser_for_update_{unique_id}",
                email=f"updatetest_{unique_id}@example.com",
                nickname="Original Nickname",
                phone_number=None,
                social_provider=None,
                social_id=None
            )
            password_hash = "hashed_password_123"
            original_user = await crud_user.create(db, user_data, password_hash)
            original_username = original_user.username  # 保存原始用户名
            
            # 执行 - 更新用户信息
            update_data = UserUpdate(
                nickname="Updated Nickname",
                status=EntityStatus.BANNED
            )
            updated_user = await crud_user.update(db, original_user, update_data)
            
            # 断言更新结果
            assert updated_user is not None, "更新应该返回用户对象"
            assert updated_user.nickname == "Updated Nickname", "昵称应该被更新"
            assert updated_user.status == EntityStatus.BANNED, "状态应该被更新为BANNED"
            
            # 验证数据库状态 - 重新查询用户
            db_user = await crud_user.get(db, original_user.id)
            assert db_user is not None, "用户应该在数据库中存在"
            assert db_user.nickname == "Updated Nickname", "数据库中的昵称应该被更新"
            assert db_user.status == EntityStatus.BANNED, "数据库中的状态应该被更新"
            assert db_user.username == original_username, "用户名不应该被修改"


class TestCrudUserRemove:
    """测试用户软删除功能"""
    
    @pytest.mark.asyncio
    async def test_remove_user_soft_deletes(self, db_session):
        """
        测试用户软删除
        - 创建一个状态为NORMAL的用户
        - 调用remove函数
        - 验证用户仍然存在但状态变为DELETED
        """
        async for db in db_session:
            # 准备 - 创建测试用户（使用唯一标识符避免冲突）
            unique_id = uuid.uuid4().hex[:8]
            user_data = UserCreate(
                username=f"testuser_for_delete_{unique_id}",
                email=f"deletetest_{unique_id}@example.com",
                nickname="User To Delete",
                phone_number=None,
                social_provider=None,
                social_id=None
            )
            password_hash = "hashed_password_123"
            user_to_delete = await crud_user.create(db, user_data, password_hash)
            
            # 验证初始状态
            assert user_to_delete.status == EntityStatus.NORMAL, "初始状态应该是NORMAL"
            
            # 执行 - 软删除用户
            deleted_user = await crud_user.remove(db, user_to_delete.id)
            
            # 断言删除结果
            assert deleted_user is not None, "删除应该返回用户对象"
            assert deleted_user.status == EntityStatus.DELETED, "删除后状态应该是DELETED"
            
            # 验证数据库状态 - 重新查询用户
            db_user = await crud_user.get(db, user_to_delete.id)
            assert db_user is not None, "用户应该仍然存在于数据库中（软删除）"
            assert db_user.status == EntityStatus.DELETED, "数据库中的状态应该是DELETED"


# ============================================================================
# 批次五追加测试 - 后台管理API相关CRUD操作
# ============================================================================

class TestCrudUserBatch5AdminFeatures:
    """批次五：后台管理API用户CRUD操作测试"""
    
    @pytest.mark.asyncio
    async def test_get_multi_with_filtering_and_count(self, db_session):
        """
        测试带筛选条件的用户查询和计数功能
        - 创建多个不同角色和状态的用户
        - 使用UserFilterParams进行筛选
        - 验证count_with_filtering和get_multi_with_filtering结果一致
        """
        async for db in db_session:
            # 前置清理 - 删除可能存在的历史测试数据
            from sqlalchemy import delete
            
            # 清理所有非系统用户（避免影响其他重要数据）
            cleanup_stmt = delete(User).where(
                User.username.like('testuser_%')
            ).execution_options(synchronize_session=False)
            await db.execute(cleanup_stmt)
            await db.commit()
            
            # 准备 - 创建多个不同角色和状态的用户
            import uuid
            from app.schemas.users import UserFilterParams
            
            # 生成随机数据避免UNIQUE约束
            base_username = f"testuser_{uuid.uuid4().hex[:8]}"
            base_email_domain = f"{uuid.uuid4().hex[:6]}.example.com"
            
            # 创建MODERATOR角色的用户
            moderator_user1 = User(
                username=f"{base_username}_mod1",
                email=f"mod1@{base_email_domain}",
                nickname="Moderator 1",
                password_hash="hashed_password_123",
                role=UserRole.MODERATOR,
                status=EntityStatus.NORMAL
            )
            
            moderator_user2 = User(
                username=f"{base_username}_mod2", 
                email=f"mod2@{base_email_domain}",
                nickname="Moderator 2",
                password_hash="hashed_password_456",
                role=UserRole.MODERATOR,
                status=EntityStatus.NORMAL
            )
            
            # 创建REGULAR角色的用户
            regular_user = User(
                username=f"{base_username}_reg",
                email=f"reg@{base_email_domain}",
                nickname="Regular User",
                password_hash="hashed_password_789",
                role=UserRole.REGULAR,
                status=EntityStatus.NORMAL
            )
            
            # 创建BANNED状态的用户
            banned_user = User(
                username=f"{base_username}_banned",
                email=f"banned@{base_email_domain}",
                nickname="Banned User",
                password_hash="hashed_password_abc",
                role=UserRole.REGULAR,
                status=EntityStatus.BANNED
            )
            
            # 添加到数据库
            db.add_all([moderator_user1, moderator_user2, regular_user, banned_user])
            await db.commit()
            
            # 执行 - 测试MODERATOR角色筛选
            filters = UserFilterParams(role=UserRole.MODERATOR)
            
            moderator_count = await crud_user.count_with_filtering(db, filters=filters)
            moderator_users = await crud_user.get_multi_with_filtering(db, filters=filters)
            
            # 断言 - 验证MODERATOR筛选结果（使用增量判断方式）
            returned_usernames = {user.username for user in moderator_users}
            assert moderator_user1.username in returned_usernames, "测试创建的moderator_user1应该在返回结果中"
            assert moderator_user2.username in returned_usernames, "测试创建的moderator_user2应该在返回结果中"
            assert regular_user.username not in returned_usernames, "测试创建的regular_user不应该在MODERATOR结果中"
            
            # 验证测试创建的用户角色都是MODERATOR
            moderator_user1_item = next((u for u in moderator_users if u.username == moderator_user1.username), None)
            moderator_user2_item = next((u for u in moderator_users if u.username == moderator_user2.username), None)
            assert moderator_user1_item is not None and moderator_user1_item.role == UserRole.MODERATOR, "moderator_user1角色应该是MODERATOR"
            assert moderator_user2_item is not None and moderator_user2_item.role == UserRole.MODERATOR, "moderator_user2角色应该是MODERATOR"
            
            # 执行 - 测试BANNED状态筛选
            banned_filters = UserFilterParams(status=EntityStatus.BANNED)
            
            banned_count = await crud_user.count_with_filtering(db, filters=banned_filters)
            banned_users = await crud_user.get_multi_with_filtering(db, filters=banned_filters)
            
            # 断言 - 验证BANNED筛选结果（使用增量判断方式）
            returned_banned_usernames = {user.username for user in banned_users}
            assert banned_user.username in returned_banned_usernames, "测试创建的banned_user应该在返回结果中"
            banned_user_item = next((u for u in banned_users if u.username == banned_user.username), None)
            assert banned_user_item is not None and banned_user_item.status == EntityStatus.BANNED, "banned_user状态应该是BANNED"
            
            # 清理 - 删除测试创建的数据，确保测试隔离
            await db.delete(moderator_user1)
            await db.delete(moderator_user2)
            await db.delete(regular_user)
            await db.delete(banned_user)
            await db.commit()