"""
CRUD用户模块新功能测试 - test_crud_user_new.py
测试新增的 get_by_social_id 和 get_by_login_identifier 方法
"""
import pytest
import uuid
from faker import Faker

from app.crud import crud_user
from app.schemas.users import UserCreate
from app.models.users import EntityStatus

fake = Faker()


class TestCRUDUserNew:
    """测试 CRUD User 新增功能"""

    @pytest.mark.asyncio
    async def test_get_by_social_id(self, db_session):
        """测试根据社交登录信息获取用户"""
        async for db in db_session:
            # 准备: 创建一个包含社交登录信息的用户
            social_provider = "authing"
            social_id = f"authing_{uuid.uuid4().hex[:10]}"
            username = f"{fake.user_name()}_{uuid.uuid4().hex[:6]}"
            email = fake.email()
            
            user_create = UserCreate(
                username=username,
                email=email,
                nickname=fake.first_name(),
                social_provider=social_provider,
                social_id=social_id
            )
            
            created_user = await crud_user.create(db, user_create, "dummy_hash")
            
            # 执行: 调用 get_by_social_id
            found_user = await crud_user.get_by_social_id(
                db, 
                provider=social_provider,
                social_id=social_id
            )
            
            # 断言: 成功找到该用户
            assert found_user is not None
            assert found_user.id == created_user.id
            assert found_user.social_provider == social_provider
            assert found_user.social_id == social_id
            
            # 测试未找到的情况
            not_found_user = await crud_user.get_by_social_id(
                db,
                provider="nonexistent_provider",
                social_id="nonexistent_id"
            )
            assert not_found_user is None

    @pytest.mark.asyncio
    async def test_get_by_login_identifier(self, db_session):
        """测试根据登录标识符获取用户（用户名、邮箱、已验证手机号）"""
        async for db in db_session:
            # 准备: 创建一个用户，手机号已验证
            username = f"{fake.user_name()}_{uuid.uuid4().hex[:6]}"
            email = fake.email()
            phone_number = f"+86{fake.random_int(min=13000000000, max=19999999999)}"
            
            user_create = UserCreate(
                username=username,
                email=email,
                nickname=fake.first_name(),
                phone_number=phone_number
            )
            
            created_user = await crud_user.create(db, user_create, "dummy_hash")
            
            # 更新用户手机号验证状态
            await crud_user.update(db, created_user, {"is_phone_verified": True})
            
            # 执行和断言: 使用用户名查找
            found_by_username = await crud_user.get_by_login_identifier(
                db, identifier=username
            )
            assert found_by_username is not None
            assert found_by_username.id == created_user.id
            
            # 执行和断言: 使用邮箱查找
            found_by_email = await crud_user.get_by_login_identifier(
                db, identifier=email
            )
            assert found_by_email is not None
            assert found_by_email.id == created_user.id
            
            # 执行和断言: 使用已验证的手机号查找
            found_by_phone = await crud_user.get_by_login_identifier(
                db, identifier=phone_number
            )
            assert found_by_phone is not None
            assert found_by_phone.id == created_user.id
            
            # 准备: 创建另一个用户，手机号未验证
            username2 = f"{fake.user_name()}_{uuid.uuid4().hex[:6]}"
            email2 = fake.email()
            phone_number2 = f"+86{fake.random_int(min=13000000000, max=19999999999)}"
            
            user_create2 = UserCreate(
                username=username2,
                email=email2,
                nickname=fake.first_name(),
                phone_number=phone_number2
            )
            
            await crud_user.create(db, user_create2, "dummy_hash")
            # 注意：不设置 is_phone_verified = True
            
            # 执行和断言: 使用未验证的手机号查找，应返回 None
            not_found_by_unverified_phone = await crud_user.get_by_login_identifier(
                db, identifier=phone_number2
            )
            assert not_found_by_unverified_phone is None
            
            # 测试不存在的标识符
            not_found = await crud_user.get_by_login_identifier(
                db, identifier="nonexistent_identifier"
            )
            assert not_found is None
