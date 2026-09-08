"""
批次五API集成测试 - 后台管理产品接口
对 app/api/v1/admin/products.py 进行集成测试
重点测试权限控制、CRUD操作和数据库状态验证
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

from app.models.users import User, UserRole, EntityStatus, MembershipProduct, MembershipProductStatus, UserMembership, MembershipStatus


class TestAdminProductsAPI:
    """后台管理产品API端点测试类"""

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
    async def test_product_endpoints_are_protected_from_regular_user(self, async_client, db_session):
        """
        测试产品管理接口受到权限保护
        - 创建REGULAR用户并获取token
        - 依次请求POST, PATCH, DELETE等所有产品管理接口
        - 验证所有请求均返回403 Forbidden
        """
        async for client in async_client:
            async for db in db_session:
                # 准备 - 创建普通用户
                base_uuid = uuid.uuid4().hex[:8]
                regular_user = User(
                    username=f"regular_user_{base_uuid}",
                    email=f"regular_{base_uuid}@test.com",
                    nickname="Regular User",
                    password_hash="hashed_password_123",
                    role=UserRole.REGULAR,
                    status=EntityStatus.NORMAL
                )
                
                db.add(regular_user)
                await db.commit()
                await db.refresh(regular_user)
                
                # 生成访问令牌（使用public_id而不是id）
                access_token = self.create_access_token(str(regular_user.public_id))
                headers = {"Authorization": f"Bearer {access_token}"}
                
                # 准备测试数据
                test_product_code = f"TEST_{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
                product_data = {
                    "code": test_product_code,
                    "name": "Test Product",
                    "description": "Test Description",
                    "price": "99.99",
                    "level": 1,
                    "duration_unit": "month",
                    "duration_value": 1,
                    "status": "DRAFT"
                }
                
                # 执行1 - 测试POST创建产品接口
                response1 = await client.post(
                    "/api/v1/admin/membership-products",
                    headers=headers,
                    json=product_data
                )
                
                # 断言1 - POST接口应该返回403
                assert response1.status_code == 403, "普通用户POST产品接口应该返回403"
                
                # 执行2 - 测试GET产品列表接口
                response2 = await client.get(
                    "/api/v1/admin/membership-products",
                    headers=headers
                )
                
                # 断言2 - GET列表接口应该返回403
                assert response2.status_code == 403, "普通用户GET产品列表接口应该返回403"
                
                # 执行3 - 测试GET单个产品接口
                response3 = await client.get(
                    f"/api/v1/admin/membership-products/{test_product_code}",
                    headers=headers
                )
                
                # 断言3 - GET单个产品接口应该返回403
                assert response3.status_code == 403, "普通用户GET单个产品接口应该返回403"
                
                # 执行4 - 测试PATCH更新产品接口
                response4 = await client.patch(
                    f"/api/v1/admin/membership-products/{test_product_code}",
                    headers=headers,
                    json={"price": "199.99"}
                )
                
                # 断言4 - PATCH接口应该返回403
                assert response4.status_code == 403, "普通用户PATCH产品接口应该返回403"
                
                # 执行5 - 测试DELETE删除产品接口
                response5 = await client.delete(
                    f"/api/v1/admin/membership-products/{test_product_code}",
                    headers=headers
                )
                
                # 断言5 - DELETE接口应该返回403
                assert response5.status_code == 403, "普通用户DELETE产品接口应该返回403"
                
                # 清理 - 删除测试创建的数据
                await db.delete(regular_user)
                await db.commit()

    @pytest.mark.asyncio
    async def test_create_product_as_admin_success(self, async_client, db_session):
        """
        测试管理员成功创建产品
        - 创建admin_user并获取token
        - 准备有效的、随机的产品创建数据
        - 使用admin的token请求POST /api/v1/admin/membership-products
        - 验证API响应和数据库状态
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
                
                # 准备 - 生成随机产品数据
                random_code = f"ADMIN_{''.join(random.choices(string.ascii_uppercase + string.digits, k=10))}"
                product_create_data = {
                    "code": random_code,
                    "name": f"管理员创建产品_{uuid.uuid4().hex[:6]}",
                    "description": "管理员创建的测试产品",
                    "price": "299.99",
                    "level": 2,
                    "duration_unit": "year",
                    "duration_value": 1,
                    "status": "ACTIVE",
                    "sort_order": 5
                }
                
                # 执行 - 管理员创建产品
                response = await client.post(
                    "/api/v1/admin/membership-products",
                    headers=admin_headers,
                    json=product_create_data
                )
                
                # 断言 API 响应
                assert response.status_code == 200, "管理员创建产品应该返回200"
                
                response_data = response.json()
                assert response_data["code"] == 200, "业务状态码应该是200"
                assert response_data["message"] == "success", "消息应该是success"
                
                # 验证响应数据与创建数据一致
                assert "data" in response_data, "响应应该包含data字段"
                created_product_data = response_data["data"]
                assert created_product_data["code"] == random_code, "返回的产品编码应该匹配"
                assert created_product_data["name"] == product_create_data["name"], "返回的产品名称应该匹配"
                assert created_product_data["price"] == product_create_data["price"], "返回的产品价格应该匹配"
                assert created_product_data["level"] == product_create_data["level"], "返回的产品等级应该匹配"
                assert created_product_data["status"] == product_create_data["status"], "返回的产品状态应该匹配"
                
                # 验证数据库状态 - 查询membership_products表
                from app.crud import crud_membership_product
                db_product = await crud_membership_product.get_by_code(db, code=random_code)
                assert db_product is not None, "新产品应该已成功创建到数据库"
                assert db_product.code == random_code, "数据库中的产品编码应该正确"
                assert db_product.name == product_create_data["name"], "数据库中的产品名称应该正确"
                assert str(db_product.price) == product_create_data["price"], "数据库中的产品价格应该正确"
                
                # 清理 - 删除测试创建的数据
                await db.delete(admin_user)
                await db.delete(db_product)
                await db.commit()

    @pytest.mark.asyncio
    async def test_get_products_list_as_admin_success(self, async_client, db_session):
        """
        测试管理员获取产品列表成功
        - 创建admin_user并获取token
        - 创建多个不同状态的产品
        - 请求GET /api/v1/admin/membership-products
        - 验证返回分页结构和产品数据
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
                
                # 准备 - 创建多个测试产品
                base_code = f"LIST_{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"
                
                active_product = MembershipProduct(
                    code=f"{base_code}_ACTIVE",
                    name=f"活跃产品_{uuid.uuid4().hex[:6]}",
                    description="活跃状态产品",
                    price=Decimal("199.99"),
                    level=1,
                    duration_unit="month",
                    duration_value=1,
                    status=MembershipProductStatus.ACTIVE,
                    sort_order=0  # 使用0确保排在最前面
                )
                
                draft_product = MembershipProduct(
                    code=f"{base_code}_DRAFT",
                    name=f"草稿产品_{uuid.uuid4().hex[:6]}",
                    description="草稿状态产品",
                    price=Decimal("99.99"),
                    level=1,
                    duration_unit="week",
                    duration_value=2,
                    status=MembershipProductStatus.DRAFT,
                    sort_order=0  # 使用0确保排在最前面（与ACTIVE相同sort_order，按created_at DESC排序）
                )
                
                # 添加到数据库
                db.add_all([admin_user, active_product, draft_product])
                await db.commit()
                await db.refresh(admin_user)
                
                # 生成管理员访问令牌
                admin_token = self.create_access_token(str(admin_user.public_id))
                admin_headers = {"Authorization": f"Bearer {admin_token}"}
                
                # 执行 - 管理员获取产品列表
                response = await client.get(
                    "/api/v1/admin/membership-products?page=1&size=10",
                    headers=admin_headers
                )
                
                # 断言 API 响应
                assert response.status_code == 200, "管理员获取产品列表应该返回200"
                
                response_data = response.json()
                assert response_data["code"] == 200, "业务状态码应该是200"
                assert response_data["message"] == "success", "消息应该是success"
                
                # 验证响应数据结构
                assert "data" in response_data, "响应应该包含data字段"
                data = response_data["data"]
                assert "total" in data, "data应该包含total字段"
                assert "page" in data, "data应该包含page字段"
                assert "size" in data, "data应该包含size字段"
                assert "items" in data, "data应该包含items字段"
                assert isinstance(data["items"], list), "items应该是列表"
                
                # 验证返回的产品包含我们创建的产品
                items = data["items"]
                assert len(items) >= 2, f"应该至少返回2个产品，实际返回{len(items)}个"
                
                # 由于排序是 sort_order ASC, created_at DESC，且数据库可能有其他产品
                # 我们创建的产品可能不在第一页，所以需要检查所有返回的产品
                # 或者查询更大的页面范围来确保找到我们创建的产品
                returned_codes = {item["code"] for item in items}
                expected_codes = {active_product.code, draft_product.code}
                
                # 如果第一页没有找到所有产品，尝试查询所有产品
                if not expected_codes.issubset(returned_codes):
                    # 查询所有产品（使用较大的size）
                    response_all = await client.get(
                        f"/api/v1/admin/membership-products?page=1&size={data['total']}",
                        headers=admin_headers
                    )
                    assert response_all.status_code == 200, "查询所有产品应该返回200"
                    all_items = response_all.json()["data"]["items"]
                    all_returned_codes = {item["code"] for item in all_items}
                    assert expected_codes.issubset(all_returned_codes), f"返回的产品应该包含我们创建的产品: {expected_codes}"
                else:
                    # 第一页就找到了所有产品
                    assert expected_codes.issubset(returned_codes), f"返回的产品应该包含我们创建的产品: {expected_codes}"
                
                # 清理 - 删除测试创建的数据
                await db.delete(admin_user)
                await db.delete(active_product)
                await db.delete(draft_product)
                await db.commit()

    @pytest.mark.asyncio
    async def test_get_product_detail_as_admin_success(self, async_client, db_session):
        """
        测试管理员获取单个产品详情成功
        - 创建admin_user并获取token
        - 创建一个测试产品
        - 请求GET /api/v1/admin/membership-products/{product_code}
        - 验证返回完整的产品信息
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
                
                # 准备 - 创建测试产品
                detail_code = f"DETAIL_{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
                test_product = MembershipProduct(
                    code=detail_code,
                    name=f"详情测试产品_{uuid.uuid4().hex[:6]}",
                    description="用于测试详情接口的产品",
                    price=Decimal("149.99"),
                    level=2,
                    duration_unit="month",
                    duration_value=3,
                    status=MembershipProductStatus.ACTIVE,
                    sort_order=5
                )
                
                # 添加到数据库
                db.add_all([admin_user, test_product])
                await db.commit()
                await db.refresh(admin_user)
                
                # 生成管理员访问令牌
                admin_token = self.create_access_token(str(admin_user.public_id))
                admin_headers = {"Authorization": f"Bearer {admin_token}"}
                
                # 执行 - 管理员获取产品详情
                response = await client.get(
                    f"/api/v1/admin/membership-products/{detail_code}",
                    headers=admin_headers
                )
                
                # 断言 API 响应
                assert response.status_code == 200, "管理员获取产品详情应该返回200"
                
                response_data = response.json()
                assert response_data["code"] == 200, "业务状态码应该是200"
                assert response_data["message"] == "success", "消息应该是success"
                
                # 验证响应数据包含完整产品信息
                assert "data" in response_data, "响应应该包含data字段"
                product_data = response_data["data"]
                assert product_data["code"] == detail_code, "产品编码应该匹配"
                assert product_data["name"] == test_product.name, "产品名称应该匹配"
                assert product_data["description"] == test_product.description, "产品描述应该匹配"
                assert product_data["price"] == "149.99", "产品价格应该匹配"
                assert product_data["level"] == test_product.level, "产品等级应该匹配"
                assert product_data["status"] == "ACTIVE", "产品状态应该匹配"
                
                # 清理 - 删除测试创建的数据
                await db.delete(admin_user)
                await db.delete(test_product)
                await db.commit()

    @pytest.mark.asyncio
    async def test_update_product_as_admin_success(self, async_client, db_session):
        """
        测试管理员成功更新产品
        - 创建admin_user并获取token
        - 创建一个测试产品
        - 使用PATCH接口更新产品信息
        - 验证API响应和数据库状态都已更新
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
                
                # 准备 - 创建待更新的产品
                update_code = f"UPDATE_{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
                original_product = MembershipProduct(
                    code=update_code,
                    name=f"原始产品_{uuid.uuid4().hex[:6]}",
                    description="原始产品描述",
                    price=Decimal("99.99"),
                    level=1,
                    duration_unit="month",
                    duration_value=1,
                    status=MembershipProductStatus.DRAFT,
                    sort_order=1
                )
                
                # 添加到数据库
                db.add_all([admin_user, original_product])
                await db.commit()
                await db.refresh(admin_user)
                
                # 生成管理员访问令牌
                admin_token = self.create_access_token(str(admin_user.public_id))
                admin_headers = {"Authorization": f"Bearer {admin_token}"}
                
                # 准备更新数据
                update_data = {
                    "name": "更新后的产品名称",
                    "description": "更新后的产品描述",
                    "price": "199.99",
                    "status": "ACTIVE"
                }
                
                # 执行 - 管理员更新产品
                response = await client.patch(
                    f"/api/v1/admin/membership-products/{update_code}",
                    headers=admin_headers,
                    json=update_data
                )
                
                # 断言 API 响应
                assert response.status_code == 200, "管理员更新产品应该返回200"
                
                response_data = response.json()
                assert response_data["code"] == 200, "业务状态码应该是200"
                assert response_data["message"] == "success", "消息应该是success"
                
                # 验证响应数据包含更新后的字段
                assert "data" in response_data, "响应应该包含data字段"
                updated_product_data = response_data["data"]
                assert updated_product_data["name"] == update_data["name"], "响应中的产品名称应该已更新"
                assert updated_product_data["description"] == update_data["description"], "响应中的产品描述应该已更新"
                assert updated_product_data["price"] == update_data["price"], "响应中的产品价格应该已更新"
                assert updated_product_data["status"] == update_data["status"], "响应中的产品状态应该已更新"
                
                # 验证数据库状态 - 重新查询产品
                from app.crud import crud_membership_product
                db_product = await crud_membership_product.get_by_code(db, code=update_code)

                await db.refresh(db_product)
                assert db_product is not None, "应该能重新查询到产品"
                assert db_product.name == update_data["name"], "数据库中的产品名称应该已更新"
                assert db_product.description == update_data["description"], "数据库中的产品描述应该已更新"
                assert str(db_product.price) == update_data["price"], "数据库中的产品价格应该已更新"
                assert db_product.status == MembershipProductStatus.ACTIVE, "数据库中的产品状态应该已更新"
                
                # 清理 - 删除测试创建的数据
                await db.delete(admin_user)
                await db.delete(db_product)
                await db.commit()

    @pytest.mark.asyncio
    async def test_delete_product_fails_if_referenced(self, async_client, db_session):
        """
        测试删除被用户订阅引用的产品失败
        - 创建admin_user并获取token
        - 创建产品product_A
        - 创建用户并为其创建订阅了product_A的记录
        - 尝试删除product_A
        - 验证返回400 Bad Request和业务错误码2006
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
                
                # 准备 - 创建普通用户
                user_uuid = uuid.uuid4().hex[:8]
                regular_user = User(
                    username=f"user_{user_uuid}",
                    email=f"user_{user_uuid}@test.com",
                    nickname="Regular User",
                    password_hash="hashed_password_user",
                    role=UserRole.REGULAR,
                    status=EntityStatus.NORMAL
                )
                
                # 准备 - 创建产品
                product_code = f"REF_{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
                referenced_product = MembershipProduct(
                    code=product_code,
                    name=f"被引用产品_{uuid.uuid4().hex[:6]}",
                    description="这个产品被用户订阅引用",
                    price=Decimal("299.99"),
                    level=1,
                    duration_unit="year",
                    duration_value=1,
                    status=MembershipProductStatus.ACTIVE,
                    sort_order=1
                )
                
                # 添加用户和产品到数据库
                db.add_all([admin_user, regular_user, referenced_product])
                await db.commit()
                await db.refresh(admin_user)
                await db.refresh(regular_user)
                
                # 准备 - 创建用户订阅记录
                user_subscription = UserMembership(
                    user_id=regular_user.id,
                    product_code=product_code,
                    transaction_id=f"test_txn_{uuid.uuid4().hex[:12]}",
                    level=1,
                    status=MembershipStatus.ACTIVE,
                    is_auto_renew=False,
                    expires_at=datetime.utcnow() + timedelta(days=365)
                )
                
                db.add(user_subscription)
                await db.commit()
                
                # 生成管理员访问令牌
                admin_token = self.create_access_token(str(admin_user.public_id))
                admin_headers = {"Authorization": f"Bearer {admin_token}"}
                
                # 执行 - 管理员尝试删除被引用的产品
                response = await client.delete(
                    f"/api/v1/admin/membership-products/{product_code}",
                    headers=admin_headers
                )
                
                # 断言 API 响应 - 应该删除失败
                assert response.status_code == 400, "删除被引用的产品应该返回400 Bad Request"
                
                response_data = response.json()
                assert response_data["code"] == 2006, "业务错误码应该是2006（业务逻辑错误）"
                assert "无法删除仍被用户订阅引用的产品" in response_data["message"], "错误消息应该提到无法删除被引用的产品"
                
                # 验证数据库状态 - 产品应该仍然存在
                from app.crud import crud_membership_product
                db_product = await crud_membership_product.get_by_code(db, code=product_code)
                assert db_product is not None, "被引用的产品应该仍然存在于数据库中（未被删除）"
                assert db_product.code == product_code, "产品编码应该保持不变"
                
                # 清理 - 删除测试创建的数据
                await db.delete(user_subscription)
                await db.delete(admin_user)
                await db.delete(regular_user)
                await db.delete(referenced_product)
                await db.commit()

    @pytest.mark.asyncio
    async def test_delete_product_success_when_no_references(self, async_client, db_session):
        """
        测试删除无引用的产品成功
        - 创建admin_user并获取token
        - 创建无用户订阅的产品
        - 删除该产品
        - 验证删除成功且产品从数据库中消失
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
                
                # 准备 - 创建无引用的产品
                delete_code = f"DEL_{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
                product_to_delete = MembershipProduct(
                    code=delete_code,
                    name=f"待删除产品_{uuid.uuid4().hex[:6]}",
                    description="这个产品没有用户订阅，可以被删除",
                    price=Decimal("99.99"),
                    level=1,
                    duration_unit="month",
                    duration_value=1,
                    status=MembershipProductStatus.DRAFT,
                    sort_order=1
                )
                
                # 添加到数据库
                db.add_all([admin_user, product_to_delete])
                await db.commit()
                await db.refresh(admin_user)
                
                # 生成管理员访问令牌
                admin_token = self.create_access_token(str(admin_user.public_id))
                admin_headers = {"Authorization": f"Bearer {admin_token}"}
                
                # 执行 - 管理员删除产品
                response = await client.delete(
                    f"/api/v1/admin/membership-products/{delete_code}",
                    headers=admin_headers
                )
                
                # 断言 API 响应 - 应该删除成功
                assert response.status_code == 200, "删除无引用的产品应该返回200"
                
                response_data = response.json()
                assert response_data["code"] == 200, "业务状态码应该是200"
                assert response_data["message"] == "success", "消息应该是success"
                assert response_data["data"] is None, "删除成功时data字段应该为null"
                
                # 验证数据库状态 - 产品应该已被物理删除
                from app.crud import crud_membership_product
                db_product = await crud_membership_product.get_by_code(db, code=delete_code)
                assert db_product is None, "产品应该已从数据库中物理删除"
                
                # 清理 - 删除测试创建的数据
                await db.delete(admin_user)
                await db.commit() 