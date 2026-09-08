"""
批次三API集成测试 - 会员产品公开接口
对 app/api/v1/endpoints/membership_products.py 进行集成测试
"""

import pytest
import uuid
from decimal import Decimal

from app.models.users import MembershipProduct, MembershipProductStatus


class TestMembershipProductsAPI:
    """会员产品API端点测试类"""

    @pytest.mark.asyncio
    async def test_get_membership_products_returns_only_active(self, async_client, db_session):
        """
        测试GET /api/v1/membership-products只返回ACTIVE状态的产品
        - 在数据库中创建多个不同状态的产品：ACTIVE, DRAFT, ARCHIVED  
        - 发送GET请求到端点
        - 验证HTTP状态码、业务状态码、返回数据结构和内容
        """
        async for client in async_client:
            async for db in db_session:
                # 准备 - 创建多个不同状态的产品（使用唯一标识符避免冲突）
                unique_id = uuid.uuid4().hex[:8]
                active_product_1 = MembershipProduct(
                    code=f"API_ACTIVE_1_{unique_id}",
                    name="API活跃产品1",
                    description="API测试活跃产品1",
                    price=Decimal("99.99"),
                    level=1,
                    duration_unit="month",
                    duration_value=1,
                    status=MembershipProductStatus.ACTIVE,
                    sort_order=1
                )
                
                active_product_2 = MembershipProduct(
                    code=f"API_ACTIVE_2_{unique_id}",
                    name="API活跃产品2", 
                    description="API测试活跃产品2",
                    price=Decimal("199.99"),
                    level=2,
                    duration_unit="year",
                    duration_value=1,
                    status=MembershipProductStatus.ACTIVE,
                    sort_order=2
                )
                
                draft_product = MembershipProduct(
                    code=f"API_DRAFT_{unique_id}",
                    name="API草稿产品",
                    description="API测试草稿产品",
                    price=Decimal("49.99"),
                    level=1,
                    duration_unit="month",
                    duration_value=1,
                    status=MembershipProductStatus.DRAFT,
                    sort_order=3
                )
                
                archived_product = MembershipProduct(
                    code=f"API_ARCHIVED_{unique_id}",
                    name="API归档产品",
                    description="API测试归档产品",
                    price=Decimal("29.99"),
                    level=1,
                    duration_unit="week",
                    duration_value=1,
                    status=MembershipProductStatus.ARCHIVED,
                    sort_order=4
                )
                
                # 添加到数据库
                db.add_all([active_product_1, active_product_2, draft_product, archived_product])
                await db.commit()
                
                # 执行 - 发送GET请求
                response = await client.get("/api/v1/membership-products")
                
                # 断言 API 响应 - HTTP状态码
                assert response.status_code == 200, "HTTP状态码应该是200"
                
                response_data = response.json()
                
                # 断言 API 响应 - 业务状态码
                assert response_data["code"] == 200, "业务状态码应该是200"
                assert response_data["message"] == "success", "消息应该是success"
                
                # 断言 API 响应 - 数据结构
                assert "data" in response_data, "响应应该包含data字段"
                assert "items" in response_data["data"], "data应该包含items字段"
                assert isinstance(response_data["data"]["items"], list), "items应该是列表"
                
                # 断言 API 响应 - 数据内容（使用增量判断方式）
                items = response_data["data"]["items"]
                
                # 验证每个返回的产品状态都是ACTIVE
                for item in items:
                    assert item["status"] == "ACTIVE", f"产品 {item['code']} 状态应该是ACTIVE"
                
                # 验证测试创建的产品在返回结果中
                returned_codes = {item["code"] for item in items}
                assert active_product_1.code in returned_codes, f"测试创建的{active_product_1.code}应该在返回结果中"
                assert active_product_2.code in returned_codes, f"测试创建的{active_product_2.code}应该在返回结果中"
                assert draft_product.code not in returned_codes, f"DRAFT状态的产品{draft_product.code}不应该在返回结果中"
                assert archived_product.code not in returned_codes, f"ARCHIVED状态的产品{archived_product.code}不应该在返回结果中"
                
                # 清理 - 删除测试创建的数据，确保测试隔离
                await db.delete(active_product_1)
                await db.delete(active_product_2)
                await db.delete(draft_product)
                await db.delete(archived_product)
                await db.commit()

    @pytest.mark.asyncio  
    async def test_get_membership_products_sorting_works(self, async_client, db_session):
        """
        测试GET /api/v1/membership-products的排序功能
        - 创建两个ACTIVE产品，设置不同的sort_order和price
        - 测试默认排序(sort_order升序)
        - 测试自定义排序(price降序)  
        - 验证排序结果正确
        """
        async for client in async_client:
            async for db in db_session:
                # 准备 - 创建两个ACTIVE产品，sort_order和price不同（使用唯一标识符避免冲突）
                unique_id = uuid.uuid4().hex[:8]
                product_a_code = f"SORT_PRODUCT_A_{unique_id}"
                product_b_code = f"SORT_PRODUCT_B_{unique_id}"
                
                product_a = MembershipProduct(
                    code=product_a_code,
                    name="排序产品A",
                    description="sort_order=10, price=100",
                    price=Decimal("100.00"),
                    level=1,
                    duration_unit="month", 
                    duration_value=1,
                    status=MembershipProductStatus.ACTIVE,
                    sort_order=10
                )
                
                product_b = MembershipProduct(
                    code=product_b_code,
                    name="排序产品B",
                    description="sort_order=5, price=200",
                    price=Decimal("200.00"),
                    level=2,
                    duration_unit="year",
                    duration_value=1,
                    status=MembershipProductStatus.ACTIVE,
                    sort_order=5
                )
                
                # 添加到数据库
                db.add_all([product_a, product_b])
                await db.commit()
                
                # 执行 1 - 测试默认排序 (sort_order升序)
                response1 = await client.get("/api/v1/membership-products")
                
                # 断言 1 - 验证默认排序
                assert response1.status_code == 200, "默认排序请求HTTP状态码应该是200"
                
                response1_data = response1.json()
                assert response1_data["code"] == 200, "默认排序业务状态码应该是200"
                
                items1 = response1_data["data"]["items"]
                # 验证测试创建的产品在结果中且排序正确
                product_a_index = next((i for i, item in enumerate(items1) if item["code"] == product_a_code), None)
                product_b_index = next((i for i, item in enumerate(items1) if item["code"] == product_b_code), None)
                
                assert product_a_index is not None, f"测试创建的{product_a_code}应该在返回结果中"
                assert product_b_index is not None, f"测试创建的{product_b_code}应该在返回结果中"
                assert product_b_index < product_a_index, f"默认排序：{product_b_code} (sort_order=5) 应该在 {product_a_code} (sort_order=10) 之前"
                
                # 执行 2 - 测试自定义排序 (price降序)
                response2 = await client.get("/api/v1/membership-products?sort=price:desc")
                
                # 断言 2 - 验证自定义排序
                assert response2.status_code == 200, "自定义排序请求HTTP状态码应该是200"
                
                response2_data = response2.json()
                assert response2_data["code"] == 200, "自定义排序业务状态码应该是200"
                
                items2 = response2_data["data"]["items"]
                # 验证测试创建的产品在价格降序排序结果中且排序正确
                product_a_index2 = next((i for i, item in enumerate(items2) if item["code"] == product_a_code), None)
                product_b_index2 = next((i for i, item in enumerate(items2) if item["code"] == product_b_code), None)
                
                assert product_a_index2 is not None, f"测试创建的{product_a_code}应该在返回结果中"
                assert product_b_index2 is not None, f"测试创建的{product_b_code}应该在返回结果中"
                assert product_b_index2 < product_a_index2, f"价格降序排序：{product_b_code} (price=200) 应该在 {product_a_code} (price=100) 之前"
                
                # 验证price值确实正确（检查测试创建的产品）
                product_a_item = next((item for item in items2 if item["code"] == product_a_code), None)
                product_b_item = next((item for item in items2 if item["code"] == product_b_code), None)
                assert product_a_item is not None, f"测试创建的{product_a_code}应该在返回结果中"
                assert product_b_item is not None, f"测试创建的{product_b_code}应该在返回结果中"
                assert float(product_a_item["price"]) == 100.00, f"{product_a_code}价格应该是100.00"
                assert float(product_b_item["price"]) == 200.00, f"{product_b_code}价格应该是200.00" 