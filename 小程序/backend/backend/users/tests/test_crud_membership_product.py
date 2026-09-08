"""
批次三CRUD单元测试 - 会员产品数据访问层
对 app/crud/crud_membership_product.py 进行详细的单元测试
"""

import pytest
import uuid
from decimal import Decimal

from app.crud import crud_membership_product
from app.models.users import MembershipProduct, MembershipProductStatus


class TestCrudMembershipProduct:
    """会员产品CRUD操作测试类"""

    @pytest.mark.asyncio
    async def test_get_multi_active_returns_only_active_products(self, db_session):
        """
        测试get_multi_active只返回ACTIVE状态的产品
        - 创建多个不同状态的产品：ACTIVE, DRAFT, ARCHIVED
        - 验证只返回ACTIVE状态的产品
        - 验证返回数量正确
        """
        async for db in db_session:
            # 准备 - 创建多个不同状态的产品（使用唯一标识符避免冲突）
            unique_id = uuid.uuid4().hex[:8]
            active_product_1 = MembershipProduct(
                code=f"ACTIVE_PRODUCT_1_{unique_id}",
                name="活跃产品1",
                description="测试活跃产品1",
                price=Decimal("99.99"),
                level=1,
                duration_unit="month",
                duration_value=1,
                status=MembershipProductStatus.ACTIVE,
                sort_order=1
            )
            
            active_product_2 = MembershipProduct(
                code=f"ACTIVE_PRODUCT_2_{unique_id}", 
                name="活跃产品2",
                description="测试活跃产品2",
                price=Decimal("199.99"),
                level=2,
                duration_unit="year",
                duration_value=1,
                status=MembershipProductStatus.ACTIVE,
                sort_order=2
            )
            
            draft_product = MembershipProduct(
                code=f"DRAFT_PRODUCT_{unique_id}",
                name="草稿产品",
                description="测试草稿产品",
                price=Decimal("49.99"),
                level=1,
                duration_unit="month",
                duration_value=1,
                status=MembershipProductStatus.DRAFT,
                sort_order=3
            )
            
            archived_product = MembershipProduct(
                code=f"ARCHIVED_PRODUCT_{unique_id}",
                name="归档产品",
                description="测试归档产品",
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
            
            # 执行 - 调用get_multi_active
            result = await crud_membership_product.get_multi_active(db)
            
            # 断言 - 验证返回结果（使用增量判断方式）
            returned_codes = {product.code for product in result}
            assert active_product_1.code in returned_codes, f"测试创建的{active_product_1.code}应该在返回结果中"
            assert active_product_2.code in returned_codes, f"测试创建的{active_product_2.code}应该在返回结果中"
            assert draft_product.code not in returned_codes, f"DRAFT状态的产品{draft_product.code}不应该在返回结果中"
            assert archived_product.code not in returned_codes, f"ARCHIVED状态的产品{archived_product.code}不应该在返回结果中"
            
            # 验证每个产品的状态都是ACTIVE
            for product in result:
                assert product.status == MembershipProductStatus.ACTIVE, f"产品 {product.code} 状态应该是ACTIVE"
            
            # 清理 - 删除测试创建的数据，确保测试隔离
            await db.delete(active_product_1)
            await db.delete(active_product_2)
            await db.delete(draft_product)
            await db.delete(archived_product)
            await db.commit()

    @pytest.mark.asyncio
    async def test_get_multi_active_returns_empty_list_when_no_active(self, db_session):
        """
        测试当没有ACTIVE产品时返回空列表
        - 只创建DRAFT和INACTIVE状态的产品
        - 验证返回空列表
        """
        async for db in db_session:
            # 准备 - 只创建非ACTIVE状态的产品（使用唯一标识符避免冲突）
            unique_id = uuid.uuid4().hex[:8]
            draft_product = MembershipProduct(
                code=f"DRAFT_ONLY_{unique_id}",
                name="仅草稿产品",
                description="测试仅草稿产品",
                price=Decimal("99.99"),
                level=1,
                duration_unit="month",
                duration_value=1,
                status=MembershipProductStatus.DRAFT,
                sort_order=1
            )
            
            inactive_product = MembershipProduct(
                code=f"INACTIVE_ONLY_{unique_id}",
                name="仅非活跃产品",
                description="测试仅非活跃产品", 
                price=Decimal("199.99"),
                level=2,
                duration_unit="year",
                duration_value=1,
                status=MembershipProductStatus.INACTIVE,
                sort_order=2
            )
            
            # 添加到数据库
            db.add_all([draft_product, inactive_product])
            await db.commit()
            
            # 执行 - 调用get_multi_active
            result = await crud_membership_product.get_multi_active(db)
            
            # 断言 - 验证返回空列表（使用增量判断方式，只验证测试创建的产品不在结果中）
            returned_codes = {product.code for product in result}
            assert draft_product.code not in returned_codes, f"DRAFT状态的产品{draft_product.code}不应该在返回结果中"
            assert inactive_product.code not in returned_codes, f"INACTIVE状态的产品{inactive_product.code}不应该在返回结果中"
            
            # 清理 - 删除测试创建的数据，确保测试隔离
            await db.delete(draft_product)
            await db.delete(inactive_product)
            await db.commit()

    @pytest.mark.asyncio
    async def test_get_multi_active_respects_default_sorting(self, db_session):
        """
        测试get_multi_active遵守默认排序(sort_order升序)
        - 创建两个ACTIVE产品，sort_order分别为10和5
        - 验证sort_order=5的产品在前面
        """
        async for db in db_session:
            # 准备 - 创建两个ACTIVE产品，sort_order不同（使用唯一标识符避免冲突）
            unique_id = uuid.uuid4().hex[:8]
            product_a_code = f"PRODUCT_A_{unique_id}"
            product_b_code = f"PRODUCT_B_{unique_id}"
            
            product_a = MembershipProduct(
                code=product_a_code,
                name="产品A",
                description="sort_order=10",
                price=Decimal("99.99"),
                level=1,
                duration_unit="month",
                duration_value=1,
                status=MembershipProductStatus.ACTIVE,
                sort_order=10
            )
            
            product_b = MembershipProduct(
                code=product_b_code, 
                name="产品B",
                description="sort_order=5",
                price=Decimal("199.99"),
                level=2,
                duration_unit="year",
                duration_value=1,
                status=MembershipProductStatus.ACTIVE,
                sort_order=5
            )
            
            # 添加到数据库
            db.add_all([product_a, product_b])
            await db.commit()
            
            # 执行 - 调用get_multi_active(不带排序参数)
            result = await crud_membership_product.get_multi_active(db)
            
            # 断言 - 验证排序结果（使用增量判断方式）
            product_a_index = next((i for i, p in enumerate(result) if p.code == product_a_code), None)
            product_b_index = next((i for i, p in enumerate(result) if p.code == product_b_code), None)
            
            assert product_a_index is not None, f"测试创建的{product_a_code}应该在返回结果中"
            assert product_b_index is not None, f"测试创建的{product_b_code}应该在返回结果中"
            assert product_b_index < product_a_index, f"默认排序：{product_b_code} (sort_order=5) 应该在 {product_a_code} (sort_order=10) 之前"
            
            # 清理 - 删除测试创建的数据，确保测试隔离
            await db.delete(product_a)
            await db.delete(product_b)
            await db.commit()

    @pytest.mark.asyncio
    async def test_get_multi_active_respects_custom_sorting(self, db_session):
        """
        测试get_multi_active遵守自定义排序(price降序)
        - 创建两个ACTIVE产品，price分别为100.00和50.00
        - 使用price:desc排序
        - 验证价格高的产品在前面
        """
        async for db in db_session:
            # 准备 - 创建两个ACTIVE产品，price不同（使用唯一标识符避免冲突）
            unique_id = uuid.uuid4().hex[:8]
            product_a_code = f"EXPENSIVE_PRODUCT_{unique_id}"
            product_b_code = f"CHEAP_PRODUCT_{unique_id}"
            
            product_a = MembershipProduct(
                code=product_a_code,
                name="高价产品",
                description="price=100.00",
                price=Decimal("100.00"),
                level=1,
                duration_unit="month",
                duration_value=1,
                status=MembershipProductStatus.ACTIVE,
                sort_order=1
            )
            
            product_b = MembershipProduct(
                code=product_b_code,
                name="低价产品", 
                description="price=50.00",
                price=Decimal("50.00"),
                level=2,
                duration_unit="year",
                duration_value=1,
                status=MembershipProductStatus.ACTIVE,
                sort_order=2
            )
            
            # 添加到数据库
            db.add_all([product_a, product_b])
            await db.commit()
            
            # 执行 - 调用get_multi_active使用自定义排序
            result = await crud_membership_product.get_multi_active(db, sort="price", direction="desc")
            
            # 断言 - 验证排序结果（使用增量判断方式）
            product_a_index = next((i for i, p in enumerate(result) if p.code == product_a_code), None)
            product_b_index = next((i for i, p in enumerate(result) if p.code == product_b_code), None)
            
            assert product_a_index is not None, f"测试创建的{product_a_code}应该在返回结果中"
            assert product_b_index is not None, f"测试创建的{product_b_code}应该在返回结果中"
            assert product_a_index < product_b_index, f"价格降序排序：{product_a_code} (price=100.00) 应该在 {product_b_code} (price=50.00) 之前"
            
            # 清理 - 删除测试创建的数据，确保测试隔离
            await db.delete(product_a)
            await db.delete(product_b)
            await db.commit() 


# ============================================================================
# 批次五追加测试 - 后台管理API相关CRUD操作
# ============================================================================

class TestCrudMembershipProductBatch5AdminFeatures:
    """批次五：后台管理API会员产品CRUD操作测试"""
    
    @pytest.mark.asyncio
    async def test_create_product_success(self, db_session):
        """
        测试成功创建会员产品
        - 使用随机数据构造MembershipProductCreate对象
        - 调用crud_membership_product.create()
        - 验证返回对象的核心字段与输入一致
        - 验证数据库状态：能够重新查询到该产品
        """
        async for db in db_session:
            # 准备 - 生成随机产品数据
            import uuid
            import string
            import random
            from decimal import Decimal
            from app.schemas.users import MembershipProductCreate
            
            random_code = f"PROD_{''.join(random.choices(string.ascii_uppercase + string.digits, k=10))}"
            random_name = f"测试产品_{uuid.uuid4().hex[:8]}"
            
            product_create_schema = MembershipProductCreate(
                code=random_code,
                name=random_name,
                description="批次五测试产品描述",
                price=Decimal("99.99"),
                level=1,
                duration_unit="month",
                duration_value=1,
                status=MembershipProductStatus.DRAFT,
                sort_order=10
            )
            
            # 执行 - 创建产品
            created_product = await crud_membership_product.create(db, obj_in=product_create_schema)
            
            # 断言 - 验证返回对象
            assert created_product is not None, "返回的MembershipProduct对象不应为None"
            assert created_product.code == product_create_schema.code, "产品编码应该匹配"
            assert created_product.name == product_create_schema.name, "产品名称应该匹配"
            assert created_product.price == product_create_schema.price, "产品价格应该匹配"
            assert created_product.level == product_create_schema.level, "产品等级应该匹配"
            assert created_product.duration_unit == product_create_schema.duration_unit, "时长单位应该匹配"
            assert created_product.duration_value == product_create_schema.duration_value, "时长数值应该匹配"
            assert created_product.status == product_create_schema.status, "产品状态应该匹配"
            
            # 验证数据库状态 - 重新查询产品
            db_product = await crud_membership_product.get_by_code(db, code=random_code)
            assert db_product is not None, "应该能从数据库中重新查询到该产品"
            assert db_product.code == random_code, "重新查询的产品编码应该正确"
            assert db_product.name == random_name, "重新查询的产品名称应该正确"
            
            # 清理 - 删除测试创建的数据
            await db.delete(created_product)
            await db.commit()

    @pytest.mark.asyncio
    async def test_create_product_fails_on_duplicate_code(self, db_session):
        """
        测试创建重复编码的产品失败
        - 先成功创建一个产品product_A
        - 尝试创建相同code的产品
        - 验证抛出IntegrityError异常
        """
        async for db in db_session:
            # 准备 - 生成随机产品数据
            import uuid
            import string
            import random
            from decimal import Decimal
            from sqlalchemy.exc import IntegrityError
            from app.schemas.users import MembershipProductCreate
            
            duplicate_code = f"DUP_{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
            
            # 第一个产品
            product_a_schema = MembershipProductCreate(
                code=duplicate_code,
                name=f"第一个产品_{uuid.uuid4().hex[:6]}",
                description="第一个产品描述",
                price=Decimal("199.99"),
                level=1,
                duration_unit="year",
                duration_value=1,
                status=MembershipProductStatus.ACTIVE
            )
            
            # 执行 - 创建第一个产品（应该成功）
            product_a = await crud_membership_product.create(db, obj_in=product_a_schema)
            assert product_a is not None, "第一个产品应该创建成功"
            
            # 准备 - 第二个产品（相同code）
            product_b_schema = MembershipProductCreate(
                code=duplicate_code,  # 相同的编码
                name=f"第二个产品_{uuid.uuid4().hex[:6]}",
                description="第二个产品描述",
                price=Decimal("299.99"),
                level=2,
                duration_unit="month",
                duration_value=6,
                status=MembershipProductStatus.DRAFT
            )
            
            # 执行和断言 - 创建重复编码的产品应该失败
            with pytest.raises(IntegrityError):
                await crud_membership_product.create(db, obj_in=product_b_schema)
            
            # 清理 - 删除测试创建的数据
            await db.delete(product_a)
            await db.commit()

    @pytest.mark.asyncio
    async def test_get_by_code_found_and_not_found(self, db_session):
        """
        测试按编码查询产品的两种情况
        - 创建产品product_A
        - 用product_A.code查询应该找到
        - 用随机不存在的code查询应该返回None
        """
        async for db in db_session:
            # 准备 - 创建测试产品
            import uuid
            import string
            import random
            from decimal import Decimal
            
            existing_code = f"EXIST_{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
            non_existing_code = f"NOEXIST_{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
            
            product_a = MembershipProduct(
                code=existing_code,
                name=f"测试产品A_{uuid.uuid4().hex[:6]}",
                description="存在的测试产品",
                price=Decimal("149.99"),
                level=1,
                duration_unit="month",
                duration_value=3,
                status=MembershipProductStatus.ACTIVE,
                sort_order=5
            )
            
            db.add(product_a)
            await db.commit()
            
            # 执行1 - 查询存在的产品
            found_product = await crud_membership_product.get_by_code(db, code=existing_code)
            
            # 断言1 - 应该找到产品
            assert found_product is not None, "应该找到存在的产品"
            assert found_product.code == existing_code, "返回产品的编码应该匹配"
            assert found_product.name == product_a.name, "返回产品的名称应该匹配"
            
            # 执行2 - 查询不存在的产品
            not_found_product = await crud_membership_product.get_by_code(db, code=non_existing_code)
            
            # 断言2 - 应该返回None
            assert not_found_product is None, "查询不存在的编码应该返回None"
            
            # 清理 - 删除测试创建的数据
            await db.delete(product_a)
            await db.commit()

    @pytest.mark.asyncio 
    async def test_get_multi_all_and_count_all(self, db_session):
        """
        测试获取所有产品和计数功能
        - 创建3个不同状态的产品（DRAFT, ACTIVE, ARCHIVED）
        - 调用count_all()和get_multi_all()
        - 验证count返回3，get_multi_all返回长度为3的列表
        """
        async for db in db_session:
            # 准备 - 创建3个不同状态的产品
            import uuid
            import string
            import random
            from decimal import Decimal
            
            base_code = f"ALL_{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"
            
            draft_product = MembershipProduct(
                code=f"{base_code}_DRAFT",
                name=f"草稿产品_{uuid.uuid4().hex[:6]}",
                description="草稿状态产品",
                price=Decimal("59.99"),
                level=1,
                duration_unit="week",
                duration_value=2,
                status=MembershipProductStatus.DRAFT,
                sort_order=1
            )
            
            active_product = MembershipProduct(
                code=f"{base_code}_ACTIVE",
                name=f"活跃产品_{uuid.uuid4().hex[:6]}",
                description="活跃状态产品", 
                price=Decimal("119.99"),
                level=2,
                duration_unit="month",
                duration_value=1,
                status=MembershipProductStatus.ACTIVE,
                sort_order=2
            )
            
            archived_product = MembershipProduct(
                code=f"{base_code}_ARCHIVED",
                name=f"归档产品_{uuid.uuid4().hex[:6]}",
                description="归档状态产品",
                price=Decimal("89.99"),
                level=1,
                duration_unit="month",
                duration_value=2,
                status=MembershipProductStatus.ARCHIVED,
                sort_order=3
            )
            
            # 添加到数据库
            db.add_all([draft_product, active_product, archived_product])
            await db.commit()
            
            # 执行 - 调用count_all和get_multi_all（使用足够大的limit确保获取所有产品）
            total_count = await crud_membership_product.count_all(db)
            all_products = await crud_membership_product.get_multi_all(db, limit=1000)
            
            # 断言 - 验证测试创建的产品在返回结果中（使用增量判断方式）
            returned_codes = {product.code for product in all_products}
            assert draft_product.code in returned_codes, f"测试创建的{draft_product.code}应该在返回结果中"
            assert active_product.code in returned_codes, f"测试创建的{active_product.code}应该在返回结果中"
            assert archived_product.code in returned_codes, f"测试创建的{archived_product.code}应该在返回结果中"
            
            # 验证返回的产品状态正确
            draft_item = next((p for p in all_products if p.code == draft_product.code), None)
            active_item = next((p for p in all_products if p.code == active_product.code), None)
            archived_item = next((p for p in all_products if p.code == archived_product.code), None)
            
            assert draft_item is not None and draft_item.status == MembershipProductStatus.DRAFT, f"{draft_product.code}状态应该是DRAFT"
            assert active_item is not None and active_item.status == MembershipProductStatus.ACTIVE, f"{active_product.code}状态应该是ACTIVE"
            assert archived_item is not None and archived_item.status == MembershipProductStatus.ARCHIVED, f"{archived_product.code}状态应该是ARCHIVED"
            
            # 清理 - 删除测试创建的数据
            await db.delete(draft_product)
            await db.delete(active_product)
            await db.delete(archived_product)
            await db.commit()

    @pytest.mark.asyncio
    async def test_update_product_price_and_status(self, db_session):
        """
        测试更新产品价格和状态
        - 创建original_product
        - 创建MembershipProductUpdate对象包含新的price和status
        - 调用crud_membership_product.update()
        - 验证数据库状态：重新查询确认字段已更新
        """
        async for db in db_session:
            # 准备 - 创建原始产品
            import uuid
            import string
            import random
            from decimal import Decimal
            from app.schemas.users import MembershipProductUpdate
            
            original_code = f"UPD_{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
            original_price = Decimal("199.99")
            original_status = MembershipProductStatus.DRAFT
            
            original_product = MembershipProduct(
                code=original_code,
                name=f"待更新产品_{uuid.uuid4().hex[:6]}",
                description="即将被更新的产品",
                price=original_price,
                level=1,
                duration_unit="year",
                duration_value=1,
                status=original_status,
                sort_order=1
            )
            
            db.add(original_product)
            await db.commit()
            
            # 准备 - 更新数据
            new_price = Decimal("249.99")
            new_status = MembershipProductStatus.ACTIVE
            new_description = "已更新的产品描述"
            
            update_data = MembershipProductUpdate(
                price=new_price,
                status=new_status,
                description=new_description
            )
            
            # 执行 - 更新产品
            updated_product = await crud_membership_product.update(
                db, db_obj=original_product, obj_in=update_data
            )
            
            # 断言 - 验证返回的更新对象
            assert updated_product is not None, "update应该返回更新后的产品对象"
            assert updated_product.price == new_price, f"价格应该已更新为{new_price}"
            assert updated_product.status == new_status, f"状态应该已更新为{new_status}"
            assert updated_product.description == new_description, "描述应该已更新"
            
            # 验证数据库状态 - 重新查询产品
            db_product = await crud_membership_product.get_by_code(db, code=original_code)
            assert db_product is not None, "应该能重新查询到产品"
            assert db_product.price == new_price, "数据库中的价格应该已更新"
            assert db_product.status == new_status, "数据库中的状态应该已更新"
            assert db_product.description == new_description, "数据库中的描述应该已更新"
            
            # 清理 - 删除测试创建的数据
            await db.delete(updated_product)
            await db.commit()

    @pytest.mark.asyncio
    async def test_remove_product_success(self, db_session):
        """
        测试成功删除产品
        - 创建product_to_delete
        - 调用crud_membership_product.remove()
        - 验证返回的对象是被删除的产品
        - 验证数据库状态：重新查询应该返回None
        """
        async for db in db_session:
            # 准备 - 创建待删除产品
            import uuid
            import string
            import random
            from decimal import Decimal
            
            delete_code = f"DEL_{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
            
            product_to_delete = MembershipProduct(
                code=delete_code,
                name=f"待删除产品_{uuid.uuid4().hex[:6]}",
                description="这个产品将被删除",
                price=Decimal("99.99"),
                level=1,
                duration_unit="month",
                duration_value=1,
                status=MembershipProductStatus.DRAFT,
                sort_order=1
            )
            
            db.add(product_to_delete)
            await db.commit()
            
            # 验证产品存在
            existing_product = await crud_membership_product.get_by_code(db, code=delete_code)
            assert existing_product is not None, "删除前产品应该存在"
            
            # 执行 - 删除产品
            deleted_product = await crud_membership_product.remove(db, code=delete_code)
            
            # 断言 - 验证删除返回值
            assert deleted_product is not None, "remove应该返回被删除的产品对象"
            assert deleted_product.code == delete_code, "返回的对象应该是被删除的产品"
            
            # 验证数据库状态 - 产品应该已被物理删除
            db_product = await crud_membership_product.get_by_code(db, code=delete_code)
            assert db_product is None, "删除后重新查询应该返回None，确认已被物理删除" 