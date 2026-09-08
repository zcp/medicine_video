"""
批次五API集成测试 - 后台管理订阅接口
对 app/api/v1/admin/subscriptions.py 进行集成测试
重点测试权限控制、订阅管理功能和数据库状态验证
"""

import pytest
import jwt
import uuid
import os
import string
import random
from datetime import datetime, timedelta
from decimal import Decimal

# 确保测试环境有JWT密钥（如果未设置，使用测试后备值）
if not os.getenv("JWT_SECRET_KEY"):
    os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-only"

from app.models.users import (
    User, UserRole, EntityStatus, 
    MembershipProduct, MembershipProductStatus,
    UserMembership, MembershipStatus
)


class TestAdminSubscriptionsAPI:
    """后台管理订阅API端点测试类"""

    def create_access_token(self, user_public_id) -> str:
        """创建测试用的JWT访问令牌
        
        Args:
            user_public_id: 用户的public_id（UUID字符串或UUID对象）
        """
        from app.core.config import settings
        # 使用settings中的JWT配置，确保与应用程序一致
        JWT_SECRET_KEY = settings.JWT_SECRET_KEY or "test-jwt-secret-key-for-testing-only"
        JWT_ALGORITHM = settings.JWT_ALGORITHM
        
        # 确保user_public_id是UUID字符串
        if isinstance(user_public_id, uuid.UUID):
            user_public_id = str(user_public_id)
        elif not isinstance(user_public_id, str):
            user_public_id = str(user_public_id)
        
        now = datetime.utcnow()
        payload = {
            "user_id": user_public_id,  # 使用UUID字符串
            "type": "access",
            "iat": now,
            "exp": now + timedelta(hours=1),
            "jti": str(uuid.uuid4())
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    @pytest.mark.asyncio
    async def test_admin_get_user_subscriptions_success(self, async_client, db_session):
        """
        测试管理员获取用户订阅列表成功
        - 创建admin_user并获取token
        - 创建target_user并为其创建2条订阅记录
        - 使用admin的token请求GET /api/v1/admin/subscriptions/by-user/{target_user.uuid}
        - 验证HTTP状态码、业务状态码、返回数据结构和内容
        """
        async for client in async_client:
            async for db in db_session:
                # 准备 - 创建管理员用户
                admin_uuid = uuid.uuid4().hex[:8]
                admin_user = User(
                    username=f"admin_{admin_uuid}",
                    email=f"admin_{admin_uuid}@test.com",
                    nickname="Admin User",
                    password_hash="hashed_password_admin",
                    role=UserRole.ADMIN,
                    status=EntityStatus.NORMAL
                )
                
                # 准备 - 创建目标用户
                target_uuid = uuid.uuid4().hex[:8]
                target_user = User(
                    username=f"target_{target_uuid}",
                    email=f"target_{target_uuid}@test.com",
                    nickname="Target User",
                    password_hash="hashed_password_target",
                    role=UserRole.REGULAR,
                    status=EntityStatus.NORMAL
                )
                
                # 准备 - 创建会员产品
                product_code1 = f"PROD1_{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
                product_code2 = f"PROD2_{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
                
                product1 = MembershipProduct(
                    code=product_code1,
                    name=f"产品1_{uuid.uuid4().hex[:6]}",
                    description="测试产品1",
                    price=Decimal("199.99"),
                    level=1,
                    duration_unit="year",
                    duration_value=1,
                    status=MembershipProductStatus.ACTIVE,
                    sort_order=1
                )
                
                product2 = MembershipProduct(
                    code=product_code2,
                    name=f"产品2_{uuid.uuid4().hex[:6]}",
                    description="测试产品2",
                    price=Decimal("99.99"),
                    level=2,
                    duration_unit="month",
                    duration_value=1,
                    status=MembershipProductStatus.ACTIVE,
                    sort_order=2
                )
                
                # 添加用户和产品到数据库
                db.add_all([admin_user, target_user, product1, product2])
                await db.commit()
                await db.refresh(admin_user)
                await db.refresh(target_user)
                
                # 准备 - 为目标用户创建2条订阅记录
                subscription1 = UserMembership(
                    user_id=target_user.id,
                    product_code=product_code1,
                    transaction_id=f"txn1_{uuid.uuid4().hex[:12]}",
                    level=1,
                    status=MembershipStatus.ACTIVE,
                    is_auto_renew=True,
                    start_date=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=365)
                )
                
                subscription2 = UserMembership(
                    user_id=target_user.id,
                    product_code=product_code2,
                    transaction_id=f"txn2_{uuid.uuid4().hex[:12]}",
                    level=2,
                    status=MembershipStatus.EXPIRED,
                    is_auto_renew=False,
                    start_date=datetime.utcnow() - timedelta(days=60),
                    expires_at=datetime.utcnow() - timedelta(days=30)
                )
                
                db.add_all([subscription1, subscription2])
                await db.commit()
                
                # 生成管理员访问令牌
                admin_token = self.create_access_token(str(admin_user.public_id))
                admin_headers = {"Authorization": f"Bearer {admin_token}"}
                
                # 执行 - 管理员获取用户订阅列表
                response = await client.get(
                    f"/api/v1/admin/subscriptions/by-user/{target_user.public_id}?page=1&size=10",
                    headers=admin_headers
                )
                
                # 断言 API 响应 - HTTP状态码
                assert response.status_code == 200, "管理员获取用户订阅列表应该返回200"
                
                response_data = response.json()
                
                # 断言 API 响应 - 业务状态码
                assert response_data["code"] == 200, "业务状态码应该是200"
                assert response_data["message"] == "success", "消息应该是success"
                
                # 断言 API 响应 - 数据结构
                assert "data" in response_data, "响应应该包含data字段"
                data = response_data["data"]
                assert "total" in data, "data应该包含total字段"
                assert "page" in data, "data应该包含page字段"
                assert "size" in data, "data应该包含size字段"
                assert "items" in data, "data应该包含items字段"
                assert isinstance(data["items"], list), "items应该是列表"
                
                # 断言 API 响应 - 数据内容
                items = data["items"]
                assert len(items) == 2, f"应该返回2条订阅记录，实际返回{len(items)}条"
                
                # 验证订阅记录的内容
                returned_product_codes = {item["product_code"] for item in items}
                expected_codes = {product_code1, product_code2}
                assert returned_product_codes == expected_codes, f"返回的产品编码应该是{expected_codes}"
                
                # 验证订阅状态
                status_map = {item["product_code"]: item["status"] for item in items}
                assert status_map[product_code1] == "ACTIVE", "产品1的订阅状态应该是ACTIVE"
                assert status_map[product_code2] == "EXPIRED", "产品2的订阅状态应该是EXPIRED"
                
                # 清理 - 删除测试创建的数据
                await db.delete(subscription1)
                await db.delete(subscription2)
                await db.delete(admin_user)
                await db.delete(target_user)
                await db.delete(product1)
                await db.delete(product2)
                await db.commit()

    @pytest.mark.asyncio
    async def test_admin_create_subscription_for_user_success(self, async_client, db_session):
        """
        测试管理员为用户手动创建订阅成功
        - 创建admin_user并获取token
        - 创建target_user和可用的product
        - 使用admin的token请求POST /api/v1/admin/subscriptions/by-user/{target_user.uuid}
        - 验证API响应和数据库状态：为target_user新增了一条订阅记录
        """
        async for client in async_client:
            async for db in db_session:
                # 准备 - 创建管理员用户
                admin_uuid = uuid.uuid4().hex[:8]
                admin_user = User(
                    username=f"admin_{admin_uuid}",
                    email=f"admin_{admin_uuid}@test.com",
                    nickname="Admin User",
                    password_hash="hashed_password_admin",
                    role=UserRole.ADMIN,
                    status=EntityStatus.NORMAL
                )
                
                # 准备 - 创建目标用户
                target_uuid = uuid.uuid4().hex[:8]
                target_user = User(
                    username=f"target_{target_uuid}",
                    email=f"target_{target_uuid}@test.com",
                    nickname="Target User",
                    password_hash="hashed_password_target",
                    role=UserRole.REGULAR,
                    status=EntityStatus.NORMAL
                )
                
                # 准备 - 创建会员产品
                product_code = f"CREATE_{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
                product = MembershipProduct(
                    code=product_code,
                    name=f"创建订阅测试产品_{uuid.uuid4().hex[:6]}",
                    description="用于测试管理员创建订阅的产品",
                    price=Decimal("299.99"),
                    level=3,
                    duration_unit="year",
                    duration_value=1,
                    status=MembershipProductStatus.ACTIVE,
                    sort_order=1
                )
                
                # 添加到数据库
                db.add_all([admin_user, target_user, product])
                await db.commit()
                await db.refresh(admin_user)
                await db.refresh(target_user)
                
                # 生成管理员访问令牌
                admin_token = self.create_access_token(str(admin_user.public_id))
                admin_headers = {"Authorization": f"Bearer {admin_token}"}
                
                # 准备订阅创建数据
                start_date = datetime.utcnow()
                expires_at = start_date + timedelta(days=365)
                transaction_id = f"manual_gift_by_admin_{uuid.uuid4().hex[:12]}"
                
                subscription_data = {
                    "product_code": product_code,
                    "transaction_id": transaction_id,
                    "start_date": start_date.isoformat() + "Z",
                    "expires_at": expires_at.isoformat() + "Z",
                    "admin_notes": "管理员手动赠送的年度会员"
                }
                
                # 执行 - 管理员为用户创建订阅
                response = await client.post(
                    f"/api/v1/admin/subscriptions/by-user/{target_user.public_id}",
                    headers=admin_headers,
                    json=subscription_data
                )
                
                # 断言 API 响应
                assert response.status_code == 200, "管理员创建用户订阅应该返回200"
                
                response_data = response.json()
                assert response_data["code"] == 200, "业务状态码应该是200"
                assert response_data["message"] == "success", "消息应该是success"
                
                # 验证返回的新订阅数据
                assert "data" in response_data, "响应应该包含data字段"
                new_subscription_data = response_data["data"]
                assert new_subscription_data["user_id"] == target_user.id, "订阅应该属于目标用户"
                assert new_subscription_data["product_code"] == product_code, "产品编码应该匹配"
                assert new_subscription_data["level"] == 3, "会员等级应该匹配产品等级"
                assert new_subscription_data["status"] == "ACTIVE", "订阅状态应该是ACTIVE"
                assert new_subscription_data["is_auto_renew"] == False, "手动创建的订阅应该默认不自动续费"
                assert new_subscription_data["transaction_id"] == transaction_id, "交易ID应该匹配"
                
                # 验证数据库状态 - 查询user_memberships表
                from app.crud import crud_user_membership
                db_subscriptions = await crud_user_membership.get_multi_by_user_id(
                    db, user_id=target_user.id
                )
                assert len(db_subscriptions) == 1, f"target_user应该有1条订阅记录，实际有{len(db_subscriptions)}条"
                
                db_subscription = db_subscriptions[0]
                assert db_subscription.product_code == product_code, "数据库中的产品编码应该正确"
                assert db_subscription.status == MembershipStatus.ACTIVE, "数据库中的订阅状态应该是ACTIVE"
                assert db_subscription.level == 3, "数据库中的会员等级应该正确"
                assert db_subscription.transaction_id == transaction_id, "数据库中的交易ID应该正确"
                
                # 清理 - 删除测试创建的数据
                await db.delete(db_subscription)
                await db.delete(admin_user)
                await db.delete(target_user)
                await db.delete(product)
                await db.commit()

    @pytest.mark.asyncio
    async def test_admin_update_subscription_success(self, async_client, db_session):
        """
        测试管理员更新订阅成功
        - 创建admin_user并获取token
        - 为target_user创建一条status为ACTIVE的订阅
        - 使用admin的token请求PATCH /api/v1/admin/subscriptions/{subscription.uuid}
        - 验证API响应和数据库状态：订阅记录的status字段已被修改
        """
        async for client in async_client:
            async for db in db_session:
                # 准备 - 创建管理员用户
                admin_uuid = uuid.uuid4().hex[:8]
                admin_user = User(
                    username=f"admin_{admin_uuid}",
                    email=f"admin_{admin_uuid}@test.com",
                    nickname="Admin User",
                    password_hash="hashed_password_admin",
                    role=UserRole.ADMIN,
                    status=EntityStatus.NORMAL
                )
                
                # 准备 - 创建目标用户
                target_uuid = uuid.uuid4().hex[:8]
                target_user = User(
                    username=f"target_{target_uuid}",
                    email=f"target_{target_uuid}@test.com",
                    nickname="Target User",
                    password_hash="hashed_password_target",
                    role=UserRole.REGULAR,
                    status=EntityStatus.NORMAL
                )
                
                # 准备 - 创建会员产品
                product_code = f"UPDATE_{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
                product = MembershipProduct(
                    code=product_code,
                    name=f"更新订阅测试产品_{uuid.uuid4().hex[:6]}",
                    description="用于测试管理员更新订阅的产品",
                    price=Decimal("199.99"),
                    level=2,
                    duration_unit="month",
                    duration_value=6,
                    status=MembershipProductStatus.ACTIVE,
                    sort_order=1
                )
                
                # 添加用户和产品到数据库
                db.add_all([admin_user, target_user, product])
                await db.commit()
                await db.refresh(admin_user)
                await db.refresh(target_user)
                
                # 准备 - 创建待更新的订阅记录
                original_expires = datetime.utcnow() + timedelta(days=180)
                subscription = UserMembership(
                    user_id=target_user.id,
                    product_code=product_code,
                    transaction_id=f"update_test_{uuid.uuid4().hex[:12]}",
                    level=2,
                    status=MembershipStatus.ACTIVE,
                    is_auto_renew=True,
                    admin_notes="原始订阅记录",
                    start_date=datetime.utcnow(),
                    expires_at=original_expires
                )
                
                db.add(subscription)
                await db.commit()
                await db.refresh(subscription)
                
                # 生成管理员访问令牌
                admin_token = self.create_access_token(str(admin_user.public_id))
                admin_headers = {"Authorization": f"Bearer {admin_token}"}
                
                # 准备更新数据
                new_expires = datetime.utcnow() + timedelta(days=365)
                update_data = {
                    "status": "REFUNDED",
                    "expires_at": new_expires.isoformat() + "Z",
                    "is_auto_renew": False,
                    "admin_notes": "用户申请退款，客服 Alice 手动处理"
                }
                
                # 执行 - 管理员更新订阅
                response = await client.patch(
                    f"/api/v1/admin/subscriptions/{subscription.public_id}",
                    headers=admin_headers,
                    json=update_data
                )
                
                # 断言 API 响应
                assert response.status_code == 200, "管理员更新订阅应该返回200"
                
                response_data = response.json()
                assert response_data["code"] == 200, "业务状态码应该是200"
                assert response_data["message"] == "success", "消息应该是success"
                
                # 验证返回的更新后订阅数据
                assert "data" in response_data, "响应应该包含data字段"
                updated_subscription_data = response_data["data"]
                assert updated_subscription_data["status"] == "REFUNDED", "响应中的状态应该已更新为REFUNDED"
                assert updated_subscription_data["is_auto_renew"] == False, "响应中的自动续费应该已更新为False"
                assert "用户申请退款" in updated_subscription_data["admin_notes"], "响应中的管理员备注应该已更新"
                
                # 验证数据库状态 - 重新查询订阅记录
                from app.crud import crud_user_membership
                db_subscription = await crud_user_membership.get_by_uuid(db, uuid=subscription.public_id)

                await db.refresh(db_subscription)
                assert db_subscription is not None, "应该能重新查询到订阅记录"
                assert db_subscription.status == MembershipStatus.REFUNDED, "数据库中的状态应该已更新为REFUNDED"
                assert db_subscription.is_auto_renew == False, "数据库中的自动续费应该已更新为False"
                assert "用户申请退款" in db_subscription.admin_notes, "数据库中的管理员备注应该已更新"
                
                # 清理 - 删除测试创建的数据
                await db.delete(db_subscription)
                await db.delete(admin_user)
                await db.delete(target_user)
                await db.delete(product)
                await db.commit()

    @pytest.mark.asyncio
    async def test_admin_get_user_subscriptions_user_not_found(self, async_client, db_session):
        """
        测试管理员查询不存在用户的订阅返回404
        - 创建admin_user并获取token
        - 使用不存在的用户UUID查询订阅
        - 验证返回404 Not Found
        """
        async for client in async_client:
            async for db in db_session:
                # 准备 - 创建管理员用户
                admin_uuid = uuid.uuid4().hex[:8]
                admin_user = User(
                    username=f"admin_{admin_uuid}",
                    email=f"admin_{admin_uuid}@test.com",
                    nickname="Admin User",
                    password_hash="hashed_password_admin",
                    role=UserRole.ADMIN,
                    status=EntityStatus.NORMAL
                )
                
                db.add(admin_user)
                await db.commit()
                await db.refresh(admin_user)
                
                # 生成管理员访问令牌
                admin_token = self.create_access_token(str(admin_user.public_id))
                admin_headers = {"Authorization": f"Bearer {admin_token}"}
                
                # 准备 - 生成不存在的用户UUID
                non_existing_user_uuid = uuid.uuid4()
                
                # 执行 - 查询不存在用户的订阅
                response = await client.get(
                    f"/api/v1/admin/subscriptions/by-user/{non_existing_user_uuid}",
                    headers=admin_headers
                )
                
                # 断言 API 响应
                assert response.status_code == 404, "查询不存在用户的订阅应该返回404"
                
                response_data = response.json()
                assert response_data["code"] == 2004, "业务错误码应该是2004（资源不存在）"
                assert "目标用户不存在" in response_data["message"]
                
                # 清理 - 删除测试创建的数据
                await db.delete(admin_user)
                await db.commit()

    @pytest.mark.asyncio
    async def test_admin_create_subscription_fails_for_invalid_product(self, async_client, db_session):
        """
        测试管理员为用户创建订阅时产品不存在失败
        - 创建admin_user和target_user
        - 使用不存在的product_code创建订阅
        - 验证返回400 Bad Request
        """
        async for client in async_client:
            async for db in db_session:
                # 准备 - 创建管理员用户
                admin_uuid = uuid.uuid4().hex[:8]
                admin_user = User(
                    username=f"admin_{admin_uuid}",
                    email=f"admin_{admin_uuid}@test.com",
                    nickname="Admin User",
                    password_hash="hashed_password_admin",
                    role=UserRole.ADMIN,
                    status=EntityStatus.NORMAL
                )
                
                # 准备 - 创建目标用户
                target_uuid = uuid.uuid4().hex[:8]
                target_user = User(
                    username=f"target_{target_uuid}",
                    email=f"target_{target_uuid}@test.com",
                    nickname="Target User",
                    password_hash="hashed_password_target",
                    role=UserRole.REGULAR,
                    status=EntityStatus.NORMAL
                )
                
                # 添加到数据库
                db.add_all([admin_user, target_user])
                await db.commit()
                await db.refresh(admin_user)
                await db.refresh(target_user)
                
                # 生成管理员访问令牌
                admin_token = self.create_access_token(str(admin_user.public_id))
                admin_headers = {"Authorization": f"Bearer {admin_token}"}
                
                # 准备 - 使用不存在的产品编码
                invalid_product_code = f"INVALID_{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
                
                subscription_data = {
                    "product_code": invalid_product_code,
                    "transaction_id": f"invalid_test_{uuid.uuid4().hex[:12]}",
                    "start_date": datetime.utcnow().isoformat() + "Z",
                    "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat() + "Z",
                    "admin_notes": "测试无效产品编码"
                }
                
                # 执行 - 尝试为用户创建无效产品的订阅
                response = await client.post(
                    f"/api/v1/admin/subscriptions/by-user/{target_user.public_id}",
                    headers=admin_headers,
                    json=subscription_data
                )
                
                # 断言 API 响应
                assert response.status_code == 404, "使用无效产品编码创建订阅应该返回404"
                
                response_data = response.json()
                assert response_data["code"] == 2004, "业务错误码应该是2004（资源不存在）"
                assert "指定的产品编码不存在" in response_data["message"], "错误消息应该提到产品编码不存在"
                
                # 清理 - 删除测试创建的数据
                await db.delete(admin_user)
                await db.delete(target_user)
                await db.commit() 