"""
用户会员订阅CRUD单元测试 - 用户功能服务
对app/crud/crud_user_membership.py中的每个函数进行详细的单元测试
"""

import pytest
import uuid
import random
import string
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy.exc import IntegrityError

from app.crud import crud_user_membership
from app.schemas.users import UserMembershipCreate, UserMembershipUpdate
from app.models.users import User, MembershipProduct, UserMembership, MembershipStatus, MembershipProductStatus
from .conftest import create_test_user

fake = Faker()


async def create_test_membership_product(db, code=None, name=None, price="99.99"):
    """创建测试会员产品的辅助函数"""
    if code is None:
        code = f"PROD_{''.join(random.choices(string.ascii_uppercase + string.digits, k=10))}"
    if name is None:
        name = fake.catch_phrase()
    
    product = MembershipProduct(
        code=code,
        name=name,
        description=fake.text(max_nb_chars=200),
        price=price,
        level=1,
        duration_unit="month",
        duration_value=1,
        status=MembershipProductStatus.ACTIVE,
        sort_order=0
    )
    
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def create_test_membership(db, user_id: int, product_code: str, status=MembershipStatus.ACTIVE):
    """创建测试用户会员订阅的辅助函数"""
    membership_data = UserMembershipCreate(
        user_id=user_id,
        product_code=product_code,
        transaction_id=f"txn_{uuid.uuid4().hex}",
        level=1,
        status=status,
        is_auto_renew=True,
        start_date=datetime.now(),
        expires_at=datetime.now() + timedelta(days=30)
    )
    
    return await crud_user_membership.create(db, obj_in=membership_data)


class TestCrudUserMembershipCreate:
    """测试用户会员订阅创建功能"""
    
    @pytest.mark.asyncio
    async def test_create_user_membership_success(self, db_session):
        """
        测试成功创建用户会员订阅
        - 准备 (Arrange): 创建一个User和一个MembershipProduct。构造一个合法的schemas.UserMembershipCreate对象。
        - 执行 (Act): 调用crud_user_membership.create()。
        - 断言 (Assert): 
          a. 断言返回的UserMembership对象不为None。
          b. 断言其user_id和product_code与输入一致。
          c. 查询数据库，确认新行已成功插入。
        """
        async for db in db_session:
            # 准备 (Arrange) - 使用随机数据
            username = f"{fake.user_name()}_{uuid.uuid4().hex[:6]}"
            email = fake.email()
            user = await create_test_user(db, username, email)
            product = await create_test_membership_product(db)
            
            membership_data = UserMembershipCreate(
                user_id=user.id,
                product_code=product.code,
                transaction_id=f"txn_{uuid.uuid4().hex}",
                level=1,
                status=MembershipStatus.ACTIVE,
                is_auto_renew=True,
                start_date=datetime.now(),
                expires_at=datetime.now() + timedelta(days=365)
            )
            
            # 执行 (Act)
            result = await crud_user_membership.create(db, obj_in=membership_data)
            
            # 断言 (Assert)
            # a. 断言返回的UserMembership对象不为None
            assert result is not None, "返回的UserMembership对象不应为None"
            
            # b. 断言其user_id和product_code与输入一致
            assert result.user_id == membership_data.user_id, "user_id应该匹配"
            assert result.product_code == membership_data.product_code, "product_code应该匹配"
            assert result.transaction_id == membership_data.transaction_id, "transaction_id应该匹配"
            assert result.level == membership_data.level, "level应该匹配"
            assert result.status == membership_data.status, "status应该匹配"
            assert result.is_auto_renew == membership_data.is_auto_renew, "is_auto_renew应该匹配"
            
            # c. 查询数据库，确认新行已成功插入
            from sqlalchemy.future import select
            stmt = select(UserMembership).where(UserMembership.id == result.id)
            db_result = await db.execute(stmt)
            db_membership = db_result.scalar_one_or_none()
            
            assert db_membership is not None, "数据库中应该存在新创建的订阅记录"
            assert db_membership.user_id == user.id, "数据库记录的user_id应该正确"
            assert db_membership.product_code == product.code, "数据库记录的product_code应该正确"


class TestCrudUserMembershipQuery:
    """测试用户会员订阅查询功能"""
    
    @pytest.mark.asyncio
    async def test_get_multi_by_user_id(self, db_session):
        """
        测试获取用户的多个订阅记录
        - 准备: 创建两个用户user_A和user_B。为user_A创建两条订阅记录，为user_B创建一条。
        - 执行: 调用crud_user_membership.get_multi_by_user_id(user_id=user_A.id)。
        - 断言: 断言返回的列表长度为2，且两条记录的user_id都等于user_A.id。
        """
        async for db in db_session:
            # 准备 - 使用随机数据
            username_a = f"{fake.user_name()}_{uuid.uuid4().hex[:6]}"
            email_a = fake.email()
            user_a = await create_test_user(db, username_a, email_a)
            
            username_b = f"{fake.user_name()}_{uuid.uuid4().hex[:6]}"
            email_b = fake.email()
            user_b = await create_test_user(db, username_b, email_b)
            
            product1 = await create_test_membership_product(db)
            product2 = await create_test_membership_product(db)
            
            # 为user_A创建两条订阅记录
            await create_test_membership(db, user_a.id, product1.code)
            await create_test_membership(db, user_a.id, product2.code)
            
            # 为user_B创建一条订阅记录
            await create_test_membership(db, user_b.id, product1.code)
            
            # 执行
            result = await crud_user_membership.get_multi_by_user_id(db, user_id=user_a.id)
            
            # 断言
            assert len(result) == 2, "user_A应该有2条订阅记录"
            for membership in result:
                assert membership.user_id == user_a.id, "所有记录的user_id都应该等于user_A.id"
            
            # 验证user_B只有一条记录
            result_b = await crud_user_membership.get_multi_by_user_id(db, user_id=user_b.id)
            assert len(result_b) == 1, "user_B应该有1条订阅记录"
            assert result_b[0].user_id == user_b.id, "记录的user_id应该等于user_B.id"
    
    @pytest.mark.asyncio
    async def test_get_by_uuid_and_user_id_success(self, db_session):
        """
        测试根据UUID和用户ID成功获取订阅记录
        - 准备: 为用户user_A创建一条订阅记录，获取其uuid。
        - 执行: 使用正确的uuid和user_id调用crud_user_membership.get_by_uuid_and_user_id()。
        - 断言: 断言返回了正确的订阅对象。
        """
        async for db in db_session:
            # 准备 - 使用随机数据
            username_a = f"{fake.user_name()}_{uuid.uuid4().hex[:6]}"
            email_a = fake.email()
            user_a = await create_test_user(db, username_a, email_a)
            product = await create_test_membership_product(db)
            
            membership = await create_test_membership(db, user_a.id, product.code)
            membership_uuid = membership.public_id
            
            # 执行
            result = await crud_user_membership.get_by_uuid_and_user_id(
                db, uuid=membership_uuid, user_id=user_a.id
            )
            
            # 断言
            assert result is not None, "应该返回正确的订阅对象"
            assert result.public_id == membership_uuid, "返回的订阅UUID应该匹配"
            assert result.user_id == user_a.id, "返回的订阅user_id应该匹配"
            assert result.id == membership.id, "返回的订阅ID应该匹配"
    
    @pytest.mark.asyncio
    async def test_get_by_uuid_and_user_id_fails_for_wrong_user(self, db_session):
        """
        测试使用错误用户ID获取订阅记录失败
        - 准备: 为user_A创建订阅记录，获取其uuid。创建一个user_B。
        - 执行: 使用user_A的uuid和user_B的user_id调用get_by_uuid_and_user_id()。
        - 断言: 断言返回结果为None。
        """
        async for db in db_session:
            # 准备 - 使用随机数据
            username_a = f"{fake.user_name()}_{uuid.uuid4().hex[:6]}"
            email_a = fake.email()
            user_a = await create_test_user(db, username_a, email_a)
            
            username_b = f"{fake.user_name()}_{uuid.uuid4().hex[:6]}"
            email_b = fake.email()
            user_b = await create_test_user(db, username_b, email_b)
            
            product = await create_test_membership_product(db)
            
            membership = await create_test_membership(db, user_a.id, product.code)
            membership_uuid = membership.public_id
            
            # 执行 - 使用user_A的uuid和user_B的user_id
            result = await crud_user_membership.get_by_uuid_and_user_id(
                db, uuid=membership_uuid, user_id=user_b.id
            )
            
            # 断言
            assert result is None, "使用错误用户ID应该返回None"


class TestCrudUserMembershipUpdate:
    """测试用户会员订阅更新功能"""
    
    @pytest.mark.asyncio
    async def test_update_user_membership(self, db_session):
        """
        测试更新用户会员订阅
        - 准备: 创建一条is_auto_renew=True的订阅记录。
        - 执行: 调用crud_user_membership.update()将is_auto_renew修改为False。
        - 断言: 重新查询该记录，断言is_auto_renew字段的值已变为False。
        """
        async for db in db_session:
            # 准备 - 使用随机数据
            username = f"{fake.user_name()}_{uuid.uuid4().hex[:6]}"
            email = fake.email()
            user = await create_test_user(db, username, email)
            product = await create_test_membership_product(db)
            
            # 创建is_auto_renew=True的订阅记录
            membership = await create_test_membership(db, user.id, product.code)
            assert membership.is_auto_renew == True, "初始状态应该是自动续费"
            
            # 执行 - 将is_auto_renew修改为False
            update_data = UserMembershipUpdate(is_auto_renew=False)
            updated_membership = await crud_user_membership.update(
                db, db_obj=membership, obj_in=update_data
            )
            
            # 断言 - 检查返回的对象
            assert updated_membership.is_auto_renew == False, "更新后is_auto_renew应该为False"
            
            # 重新查询该记录，确认数据库状态
            from sqlalchemy.future import select
            stmt = select(UserMembership).where(UserMembership.id == membership.id)
            db_result = await db.execute(stmt)
            db_membership = db_result.scalar_one_or_none()
            
            assert db_membership is not None, "数据库中应该存在该订阅记录"
            assert db_membership.is_auto_renew == False, "数据库中is_auto_renew字段应该已更新为False" 