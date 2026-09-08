"""
用户订阅管理API集成测试 - 用户功能服务
对批次四的用户侧订阅管理API端点进行集成测试
"""

import pytest
import uuid
import random
import string
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy.future import select

from app.models.users import User, MembershipProduct, UserMembership, MembershipStatus, MembershipProductStatus
from .conftest import create_test_user, create_captcha_mock_data

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
    membership = UserMembership(
        user_id=user_id,
        product_code=product_code,
        transaction_id=f"txn_{uuid.uuid4().hex}",
        level=1,
        status=status,
        is_auto_renew=True,
        start_date=datetime.now(),
        expires_at=datetime.now() + timedelta(days=30)
    )
    
    db.add(membership)
    await db.commit()
    await db.refresh(membership)
    return membership


async def get_access_token_for_user(client, db, username=None, email=None):
    """获取用户访问令牌的辅助函数"""
    # 使用随机数据生成用户名和邮箱
    if username is None:
        username = f"{fake.user_name()}_{uuid.uuid4().hex[:6]}"
    if email is None:
        email = fake.email()
    
    # 创建用户
    user = await create_test_user(db, username, email)
    
    # 获取验证码数据
    captcha_data = create_captcha_mock_data()
    
    # 登录请求
    login_data = {
        "username": username,
        "password": "testpassword123",
        "captcha_id": captcha_data["captcha_id"],
        "captcha_solution": captcha_data["captcha_solution"],
        "agreed_to_terms": True,
    }
    
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200, "登录应该成功"
    
    response_data = response.json()
    access_token = response_data["data"]["access_token"]
    
    return user, access_token


class TestGetMyMemberships:
    """测试获取当前用户的会员订阅列表API"""
    
    @pytest.mark.asyncio
    async def test_get_my_memberships_success(self, async_client, db_session, mock_redis_captcha_success):
        """
        测试成功获取用户订阅列表
        - 准备: 创建一个用户test_user并为其生成access_token。为该用户在数据库中创建两条订阅记录。
        - 执行: 使用该token请求GET /api/v1/users/me/memberships。
        - 断言API响应:
          a. 断言HTTP状态码为200，业务code为200。
          b. 断言data['items']列表的长度为2。
          c. 断言列表中每个元素的user_id都与test_user.id匹配。
        """
        async for client in async_client:
            async for db in db_session:
                # 准备 - 创建用户并获取access_token（使用随机数据）
                test_user, access_token = await get_access_token_for_user(client, db)
                
                # 为该用户在数据库中创建两条订阅记录
                product1 = await create_test_membership_product(db, price="99.99")
                product2 = await create_test_membership_product(db, price="199.99")
                
                membership1 = await create_test_membership(db, test_user.id, product1.code)
                membership2 = await create_test_membership(db, test_user.id, product2.code)
                
                # 执行 - 使用token请求订阅列表
                headers = {"Authorization": f"Bearer {access_token}"}
                response = await client.get("/api/v1/users/me/memberships", headers=headers)
                
                # 断言API响应
                # a. 断言HTTP状态码为200，业务code为200
                assert response.status_code == 200, "HTTP状态码应该是200"
                
                response_data = response.json()
                assert response_data["code"] == 200, "业务状态码应该是200"
                assert response_data["message"] == "success", "消息应该是success"
                
                # b. 断言data['items']列表的长度为2
                data = response_data["data"]
                assert "items" in data, "响应应该包含items字段"
                assert len(data["items"]) == 2, "items列表长度应该为2"
                
                # c. 断言列表中每个元素的user_id都与test_user.id匹配
                for item in data["items"]:
                    assert item["user_id"] == test_user.id, "所有订阅记录的user_id都应该匹配test_user.id"


class TestCreateSubscription:
    """测试用户购买/创建新订阅API"""
    
    @pytest.mark.asyncio
    async def test_create_subscription_success(self, async_client, db_session, mock_redis_captcha_success):
        """
        测试成功创建订阅
        - 准备: 创建用户test_user并生成access_token。创建一个ACTIVE状态的MembershipProduct。
        - 执行: 使用token请求POST /api/v1/users/me/memberships，请求体包含product_code和一个模拟的payment_token。
        - 断言API响应:
          a. 断言HTTP状态码为200，业务code为200。
          b. 断言返回的data中，status为ACTIVE，product_code正确。
        - 验证数据库状态:
          a. 查询user_memberships表，断言为test_user创建了一条新记录。
        """
        async for client in async_client:
            async for db in db_session:
                # 准备 - 创建用户并获取access_token（使用随机数据）
                test_user, access_token = await get_access_token_for_user(client, db)
                
                # 创建一个ACTIVE状态的MembershipProduct
                product = await create_test_membership_product(db, price="99.99")
                
                # 执行 - 请求创建订阅
                headers = {"Authorization": f"Bearer {access_token}"}
                request_data = {
                    "product_code": product.code,
                    "payment_token": "tok_visa_1234567890"
                }
                response = await client.post("/api/v1/users/me/memberships", json=request_data, headers=headers)
                
                # 断言API响应
                # a. 断言HTTP状态码为200，业务code为200
                assert response.status_code == 200, "HTTP状态码应该是200"
                
                response_data = response.json()
                assert response_data["code"] == 200, "业务状态码应该是200"
                assert response_data["message"] == "success", "消息应该是success"
                
                # b. 断言返回的data中，status为ACTIVE，product_code正确
                data = response_data["data"]
                assert data["status"] == "ACTIVE", "订阅状态应该是ACTIVE"
                assert data["product_code"] == product.code, "产品编码应该正确"
                
                # 验证数据库状态 - a. 查询user_memberships表，断言为test_user创建了一条新记录
                stmt = select(UserMembership).where(UserMembership.user_id == test_user.id)
                db_result = await db.execute(stmt)
                memberships = db_result.scalars().all()
                
                assert len(memberships) == 1, "应该为test_user创建了一条订阅记录"
                new_membership = memberships[0]
                assert new_membership.product_code == product.code, "数据库记录的product_code应该正确"
                assert new_membership.status == MembershipStatus.ACTIVE, "数据库记录的状态应该是ACTIVE"
    
    @pytest.mark.asyncio
    async def test_create_subscription_fails_if_already_active(self, async_client, db_session, mock_redis_captcha_success):
        """
        测试重复购买同产品订阅失败
        - 准备: 创建用户test_user，并为其已创建一条product_code='VIDEO_YEARLY'且状态为ACTIVE的订阅。为用户生成access_token。
        - 执行: 再次尝试请求POST /api/v1/users/me/memberships购买同一个product_code。
        - 断言API响应: 断言HTTP状态码为409 (Conflict)，业务code为2005。
        - 验证数据库状态: 查询user_memberships表，断言该用户的订阅总数没有增加。
        """
        async for client in async_client:
            async for db in db_session:
                # 准备 - 创建用户并获取access_token（使用随机数据）
                test_user, access_token = await get_access_token_for_user(client, db)
                
                # 创建产品并为用户创建已有的订阅
                product = await create_test_membership_product(db, price="99.99")
                existing_membership = await create_test_membership(
                    db, test_user.id, product.code, MembershipStatus.ACTIVE
                )
                
                # 验证初始状态 - 用户已有一条订阅
                stmt = select(UserMembership).where(UserMembership.user_id == test_user.id)
                db_result = await db.execute(stmt)
                initial_memberships = db_result.scalars().all()
                initial_count = len(initial_memberships)
                assert initial_count == 1, "用户应该已有一条订阅记录"
                
                # 执行 - 再次尝试购买同一个product_code
                headers = {"Authorization": f"Bearer {access_token}"}
                request_data = {
                    "product_code": product.code,
                    "payment_token": "tok_visa_1234567890"
                }
                response = await client.post("/api/v1/users/me/memberships", json=request_data, headers=headers)
                
                # 断言API响应 - 断言HTTP状态码为409 (Conflict)，业务code为2005
                assert response.status_code == 409, "HTTP状态码应该是409 (Conflict)"
                
                response_data = response.json()
                assert response_data["code"] == 2005, "业务状态码应该是2005"
                
                # 验证数据库状态 - 查询user_memberships表，断言该用户的订阅总数没有增加
                stmt = select(UserMembership).where(UserMembership.user_id == test_user.id)
                db_result = await db.execute(stmt)
                final_memberships = db_result.scalars().all()
                final_count = len(final_memberships)
                
                assert final_count == initial_count, "用户的订阅总数不应该增加"


class TestUpdateSubscription:
    """测试用户更新自己的订阅API"""
    
    @pytest.mark.asyncio
    async def test_update_subscription_auto_renew_success(self, async_client, db_session, mock_redis_captcha_success):
        """
        测试成功更新订阅自动续费设置
        - 准备: 为用户test_user创建一条is_auto_renew=True的订阅，并获取其uuid。为用户生成access_token。
        - 执行: 使用token请求PATCH /api/v1/users/me/memberships/{subscription_uuid}，请求体为{"is_auto_renew": false}。
        - 断言API响应: 断言HTTP 200，且返回的data中is_auto_renew为false。
        - 验证数据库状态: 查询数据库，确认该订阅记录的is_auto_renew字段已被更新为false。
        """
        async for client in async_client:
            async for db in db_session:
                # 准备 - 创建用户并获取access_token（使用随机数据）
                test_user, access_token = await get_access_token_for_user(client, db)
                
                # 创建产品和订阅（is_auto_renew=True）
                product = await create_test_membership_product(db, price="99.99")
                membership = await create_test_membership(db, test_user.id, product.code)
                subscription_uuid = membership.public_id
                
                # 确认初始状态
                assert membership.is_auto_renew == True, "初始状态应该是自动续费"
                
                # 执行 - 请求更新订阅
                headers = {"Authorization": f"Bearer {access_token}"}
                request_data = {"is_auto_renew": False}
                response = await client.patch(
                    f"/api/v1/users/me/memberships/{subscription_uuid}", 
                    json=request_data, 
                    headers=headers
                )
                
                # 断言API响应 - 断言HTTP 200，且返回的data中is_auto_renew为false
                assert response.status_code == 200, "HTTP状态码应该是200"
                
                response_data = response.json()
                assert response_data["code"] == 200, "业务状态码应该是200"
                assert response_data["message"] == "success", "消息应该是success"
                
                data = response_data["data"]
                assert data["is_auto_renew"] == False, "返回的is_auto_renew应该为false"
                
                # 验证数据库状态 - 查询数据库，确认该订阅记录的is_auto_renew字段已被更新为false
                stmt = select(UserMembership).where(UserMembership.id == membership.id)
                db_result = await db.execute(stmt)
                updated_membership = db_result.scalar_one_or_none()

                # 【关键】在重新查询之前，先让会话刷新该对象
                await db.refresh(membership)

                assert updated_membership is not None, "数据库中应该存在该订阅记录"
                assert updated_membership.is_auto_renew == False, "数据库中is_auto_renew字段应该已更新为False"
    
    @pytest.mark.asyncio
    async def test_update_subscription_fails_for_other_user(self, async_client, db_session, mock_redis_captcha_success):
        """
        测试用户无法更新其他用户的订阅
        - 准备: 为user_A创建一条订阅并获取其uuid。为user_B生成access_token。
        - 执行: 使用user_B的token，尝试去PATCH user_A的订阅记录。
        - 断言API响应: 断言HTTP状态码为404 (或403)，业务code为2004 (或3002)。
        """
        async for client in async_client:
            async for db in db_session:
                # 准备 - 为user_A创建一条订阅并获取其uuid（使用随机数据）
                user_a, _ = await get_access_token_for_user(client, db)
                
                product = await create_test_membership_product(db, price="99.99")
                membership_a = await create_test_membership(db, user_a.id, product.code)
                subscription_uuid = membership_a.public_id
                
                # 为user_B生成access_token（使用随机数据）
                user_b, access_token_b = await get_access_token_for_user(client, db)
                
                # 执行 - 使用user_B的token尝试更新user_A的订阅记录
                headers = {"Authorization": f"Bearer {access_token_b}"}
                request_data = {"is_auto_renew": False}
                response = await client.patch(
                    f"/api/v1/users/me/memberships/{subscription_uuid}", 
                    json=request_data, 
                    headers=headers
                )
                
                # 断言API响应 - 断言HTTP状态码为404，业务code为2004
                assert response.status_code == 404, "HTTP状态码应该是404 (Not Found)"
                
                response_data = response.json()
                assert response_data["code"] == 2004, "业务状态码应该是2004" 