"""
LiveCore Service - Experts CRUD Unit Tests

This module contains unit tests for all CRUD operations in app/crud/experts.py.
"""

import uuid
import pytest
from typing import List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from faker import Faker

# 项目内导入
from app.crud import experts as crud_experts
from app.models.experts import Expert, UserExpertSubscription, LiveSessionExpert, SessionExpertRole
from app.schemas.experts import ExpertCreate, ExpertUpdate
from app.exceptions import DatabaseIntegrityException
from app.models.live_core import LiveSession, LiveSessionStatus
from sqlalchemy.util import asyncio

# 初始化 Faker
fake = Faker()


# ==================== 辅助函数 (Helper Functions) ====================

async def create_test_expert(db: AsyncSession, **kwargs) -> Expert:
    """创建测试专家的辅助函数"""
    default_data = {
        "name": fake.name(),
        "title": fake.job(),
        "hospital": fake.company(),
        "department": fake.word(),
        "expertise_areas": fake.text(max_nb_chars=100),
        "bio": fake.text(max_nb_chars=200),
        "avatar_url": fake.image_url(),
        "is_featured": fake.boolean(),
        "sort_order": fake.random_int(min=0, max=100)
    }
    expert_data = ExpertCreate(**{**default_data, **kwargs})
    return await crud_experts.create_expert(db, expert_data)


async def create_test_subscription(
    db: AsyncSession, 
    user_id: uuid.UUID = None, 
    expert_id: uuid.UUID = None
) -> UserExpertSubscription:
    """创建测试关注记录的辅助函数"""
    if user_id is None:
        user_id = uuid.uuid4()
    if expert_id is None:
        expert = await create_test_expert(db)
        expert_id = expert.id
    return await crud_experts.create_subscription(db, user_id, expert_id)

async def create_test_session(db: AsyncSession, **kwargs):
    """创建测试LiveSession的辅助函数"""
    from app.models.live_core import LiveSession, LiveSessionStatus, LiveRoom
    from datetime import datetime
    
    # 如果没有提供room_id，先创建一个LiveRoom
    if 'room_id' not in kwargs:
        room = LiveRoom(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            title=f"测试房间_{uuid.uuid4().hex[:8]}",
            stream_key=f"stream_key_{uuid.uuid4().hex[:16]}"
        )
        db.add(room)
        await db.flush()
        kwargs['room_id'] = room.id
    
    default_data = {
        "status": LiveSessionStatus.SCHEDULED,
        "start_time": datetime.now()
    }
    session_data = {**default_data, **kwargs}
    
    session = LiveSession(
        id=uuid.uuid4(),
        **session_data
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


# ==================== Expert CRUD测试 ====================

class TestExpertCRUD:
    """Expert CRUD函数测试"""

    @pytest.mark.asyncio
    async def test_create_expert_success(self, db_session):
        """测试成功创建专家"""
        async for db in db_session:
            # 准备测试数据
            expert_data = ExpertCreate(
                name="房树强",
                title="主任医师、教授",
                hospital="北京大学人民医院",
                department="肝胆外科",
                expertise_areas="肝胆胰脾外科,微创手术",
                bio="从事肝胆外科临床工作30余年...",
                avatar_url="/media/experts/fangshuqiang.jpg",
                is_featured=True,
                sort_order=1
            )

            # 调用CRUD函数
            expert = await crud_experts.create_expert(db, expert_data)

            # 验证返回值
            assert expert.id is not None
            assert expert.name == "房树强"
            assert expert.title == "主任医师、教授"
            assert expert.hospital == "北京大学人民医院"
            assert expert.department == "肝胆外科"
            assert expert.expertise_areas == "肝胆胰脾外科,微创手术"
            assert expert.is_featured is True
            assert expert.sort_order == 1
            assert expert.created_at is not None
            assert expert.updated_at is not None

            # 验证数据库中的记录
            result = await db.execute(
                select(Expert).where(Expert.id == expert.id)
            )
            db_expert = result.scalar_one_or_none()
            assert db_expert is not None
            assert db_expert.name == "房树强"
            break

    @pytest.mark.asyncio
    async def test_create_expert_duplicate_user_id(self, db_session):
        """测试创建专家失败（user_id重复）"""
        async for db in db_session:
            # 创建第一个专家（绑定user_id）
            user_id = uuid.uuid4()
            expert1_data = ExpertCreate(
                user_id=user_id,
                name="专家1",
                title="主任医师",
                hospital="医院A",
                is_featured=False
            )
            expert1 = await crud_experts.create_expert(db, expert1_data)
            await db.commit()

            # 尝试创建第二个专家（相同user_id）
            expert2_data = ExpertCreate(
                user_id=user_id,
                name="专家2",
                title="副主任医师",
                hospital="医院B",
                is_featured=False
            )

            # 验证抛出DatabaseIntegrityException
            with pytest.raises(DatabaseIntegrityException) as exc_info:
                await crud_experts.create_expert(db, expert2_data)
            
            assert "该用户已绑定到其他专家档案" in str(exc_info.value)
            break

    @pytest.mark.asyncio
    async def test_get_expert_success(self, db_session):
        """测试成功获取专家"""
        async for db in db_session:
            # 创建测试专家
            expert = await create_test_expert(db)
            await db.commit()

            # 调用CRUD函数
            result = await crud_experts.get_expert(db, expert.id)

            # 验证返回值
            assert result is not None
            assert result.id == expert.id
            assert result.name == expert.name
            break

    @pytest.mark.asyncio
    async def test_get_expert_not_found(self, db_session):
        """测试获取不存在的专家"""
        async for db in db_session:
            non_existent_id = uuid.uuid4()

            # 调用CRUD函数
            result = await crud_experts.get_expert(db, non_existent_id)

            # 验证返回None
            assert result is None
            break

    @pytest.mark.asyncio
    async def test_get_expert_by_user_id_success(self, db_session):
        """测试根据user_id成功获取专家"""
        async for db in db_session:
            # 创建测试专家（绑定user_id）
            user_id = uuid.uuid4()
            expert = await create_test_expert(db, user_id=user_id)
            await db.commit()

            # 调用CRUD函数
            result = await crud_experts.get_expert_by_user_id(db, user_id)

            # 验证返回值
            assert result is not None
            assert result.id == expert.id
            assert result.user_id == user_id
            break

    @pytest.mark.asyncio
    async def test_get_expert_by_user_id_not_found(self, db_session):
        """测试根据user_id获取不存在的专家"""
        async for db in db_session:
            non_existent_user_id = uuid.uuid4()

            # 调用CRUD函数
            result = await crud_experts.get_expert_by_user_id(db, non_existent_user_id)

            # 验证返回None
            assert result is None
            break

    @pytest.mark.asyncio
    async def test_get_featured_experts(self, db_session):
        """测试获取推荐专家列表"""
        async for db in db_session:
            featured1 = await create_test_expert(db, is_featured=True, sort_order=0)
            featured2 = await create_test_expert(db, is_featured=True, sort_order=1)
            non_featured = await create_test_expert(db, is_featured=False)
            await db.flush()

            results = await crud_experts.get_featured_experts(db, limit=50)

            # 库中可能有残留数据，limit=50 可能未包含我们创建的两条；只验证我们创建的推荐专家至少有一条在结果中，且非推荐专家不在结果中
            our_featured = [r for r in results if r.id in [featured1.id, featured2.id]]
            assert len(our_featured) >= 1, \
                f"Expected at least 1 of our featured experts in results. " \
                f"Total results: {len(results)}, Our IDs: [{featured1.id}, {featured2.id}]"
            assert non_featured.id not in [r.id for r in results], "non_featured must not appear in featured list"
            # 验证返回的均为 is_featured=True
            assert all(r.is_featured for r in results), "get_featured_experts must return only featured experts"
            break

    @pytest.mark.asyncio
    async def test_get_experts_multi_and_total_basic(self, db_session):
        """测试分页获取专家列表（基础）"""
        async for db in db_session:
            # 创建多个专家
            for i in range(5):
                await create_test_expert(db, name=f"专家{i}")
            await db.commit()

            # 调用CRUD函数（分页）
            experts, total = await crud_experts.get_experts_multi_and_total(
                db, skip=0, limit=3
            )

            # 验证返回值
            assert len(experts) == 3
            assert total >= 5
            break

    @pytest.mark.asyncio
    async def test_get_experts_multi_and_total_with_filters(self, db_session):
        """测试分页获取专家列表（带筛选）"""
        async for db in db_session:
            # 创建不同类型的专家（使用唯一标识）
            import time
            unique_suffix = str(int(time.time() * 1000) % 100000)
            expert1 = await create_test_expert(
                db, 
                name=f"张医生{unique_suffix}", 
                hospital=f"北京医院{unique_suffix}", 
                is_featured=True,
                sort_order=0  # 确保在分页结果中排序靠前
            )
            expert2 = await create_test_expert(
                db, 
                name=f"李医生{unique_suffix}", 
                hospital=f"上海医院{unique_suffix}", 
                is_featured=False
            )
            # 不需要commit！依赖fixture的rollback清理数据

            # 按名称筛选（使用唯一后缀）
            experts, total = await crud_experts.get_experts_multi_and_total(
                db, skip=0, limit=100, name=f"张医生{unique_suffix}"
            )
            assert len(experts) >= 1, f"Expected at least 1 expert with name '张医生{unique_suffix}', got {len(experts)}"
            assert any(e.id == expert1.id for e in experts), f"expert1 not found in results"

            # 按医院筛选（使用唯一后缀）
            experts, total = await crud_experts.get_experts_multi_and_total(
                db, skip=0, limit=100, hospital=f"北京医院{unique_suffix}"
            )
            assert len(experts) >= 1, f"Expected at least 1 expert from '北京医院{unique_suffix}', got {len(experts)}"
            assert any(e.id == expert1.id for e in experts), f"expert1 not found in results"

            # 按推荐状态筛选
            experts, total = await crud_experts.get_experts_multi_and_total(
                db, skip=0, limit=100, is_featured=True
            )
            assert len(experts) >= 1, f"Expected at least 1 featured expert, got {len(experts)}"
            # 只验证我们创建的专家
            our_experts = [e for e in experts if e.id == expert1.id]
            assert len(our_experts) == 1, \
                f"expert1 not found in featured experts. " \
                f"Total featured experts: {len(experts)}, " \
                f"expert1.id: {expert1.id}, " \
                f"Result IDs (first 10): {[e.id for e in experts[:10]]}"
            assert all(e.is_featured for e in experts), f"Found non-featured expert in results"
            break

    @pytest.mark.asyncio
    async def test_get_experts_multi_and_total_with_sort(self, db_session):
        """测试分页获取专家列表（带排序）"""
        async for db in db_session:
            import time
            unique_suffix = str(int(time.time() * 1000) % 100000)

            expert1 = await create_test_expert(db, name=f"Z专家{unique_suffix}", sort_order=999999)
            expert2 = await create_test_expert(db, name=f"A专家{unique_suffix}", sort_order=999999)
            await db.flush()

            experts, total = await crud_experts.get_experts_multi_and_total(
                db, skip=0, limit=100, name=f"专家{unique_suffix}", sort="name:desc"
            )

            our_experts = [e for e in experts if e.id in [expert1.id, expert2.id]]
            assert len(our_experts) >= 1 and total >= 1, \
                f"Expected at least 1 expert matching name filter. " \
                f"Total: {total}, our_experts: {len(our_experts)}, experts: {len(experts)}"

            # ✅ 验证排序：当两个专家都在结果中时，Z应在A前面（按name DESC）
            if len(our_experts) == 2:
                expert1_in_our = next((i, e) for i, e in enumerate(our_experts) if e.id == expert1.id)
                expert2_in_our = next((i, e) for i, e in enumerate(our_experts) if e.id == expert2.id)
                assert expert1_in_our[0] < expert2_in_our[0], \
                    f"expert1 (Z) should be before expert2 (A) in name desc order"

            # ✅ 测试按name升序排序（A应该在Z前面）
            experts_asc, total_asc = await crud_experts.get_experts_multi_and_total(
                db, skip=0, limit=100, name=f"专家{unique_suffix}", sort="name:asc"
            )
            our_experts_asc = [e for e in experts_asc if e.id in [expert1.id, expert2.id]]
            assert len(our_experts_asc) >= 1 and total_asc >= 1, \
                f"Expected at least 1 expert in asc results. total_asc={total_asc}, our_experts_asc={len(our_experts_asc)}"
            if len(our_experts_asc) == 2:
                expert1_in_asc = next((i, e) for i, e in enumerate(our_experts_asc) if e.id == expert1.id)
                expert2_in_asc = next((i, e) for i, e in enumerate(our_experts_asc) if e.id == expert2.id)
                assert expert2_in_asc[0] < expert1_in_asc[0], \
                    f"expert2 (A) should be before expert1 (Z) in name asc order"

            # 方案2：测试默认排序（sort_order ASC, created_at DESC）
            # 使用与上面相同的 unique_suffix，用 name 筛选只取本用例创建的专家，避免 DB 有大量数据时前 100 条不包含我们
            expert3 = await create_test_expert(db, name=f"C专家{unique_suffix}", sort_order=999999)
            await asyncio.sleep(0.1)  # 增加延迟确保 created_at 不同
            expert4 = await create_test_expert(db, name=f"D专家{unique_suffix}", sort_order=999999)

            # 不传 sort 参数（默认排序），用 name 筛选确保结果中包含本用例的 C、D
            experts2, total2 = await crud_experts.get_experts_multi_and_total(
                db, skip=0, limit=100, name=f"专家{unique_suffix}"
            )
            our_experts2 = [e for e in experts2 if e.id in [expert3.id, expert4.id]]
            assert len(our_experts2) >= 1, f"Expected at least one of expert3/expert4 in default-sort result, got {len(our_experts2)}"

            # ✅ 仅当两个专家都在结果中时，验证相对顺序（在our_experts2中的顺序）
            if len(our_experts2) == 2:
                expert3_in_our = next((i, e) for i, e in enumerate(our_experts2) if e.id == expert3.id)
                expert4_in_our = next((i, e) for i, e in enumerate(our_experts2) if e.id == expert4.id)
                await db.refresh(expert3)
                await db.refresh(expert4)
                if expert4.created_at > expert3.created_at:
                    assert expert4_in_our[0] < expert3_in_our[0], \
                        "expert4 (newer) should be before expert3 when sort_order same, created_at desc"
                elif expert4.created_at < expert3.created_at:
                    assert expert3_in_our[0] < expert4_in_our[0], \
                        "expert3 (newer) should be before expert4 when sort_order same, created_at desc"
            else:
                # created_at相同，排序不确定，只验证两个专家都在结果中
                assert len(our_experts2) == 2, "Both experts should be in results when created_at is same"

            break

    @pytest.mark.asyncio
    async def test_update_expert_success(self, db_session):
        """测试成功更新专家"""
        async for db in db_session:
            # 创建测试专家
            expert = await create_test_expert(db, name="原名")
            await db.commit()

            # 准备更新数据
            update_data = ExpertUpdate(
                name="新名称",
                title="新职称",
                hospital="新医院"
            )

            # 调用CRUD函数
            updated_expert = await crud_experts.update_expert(
                db, expert.id, update_data
            )
            await db.commit()

            # 验证返回值
            assert updated_expert is not None
            assert updated_expert.id == expert.id
            assert updated_expert.name == "新名称"
            assert updated_expert.title == "新职称"
            assert updated_expert.hospital == "新医院"

            # 验证数据库中的记录
            result = await db.execute(
                select(Expert).where(Expert.id == expert.id)
            )
            db_expert = result.scalar_one_or_none()
            assert db_expert.name == "新名称"
            break

    @pytest.mark.asyncio
    async def test_update_expert_not_found(self, db_session):
        """测试更新不存在的专家"""
        async for db in db_session:
            non_existent_id = uuid.uuid4()
            update_data = ExpertUpdate(name="新名称")

            # 调用CRUD函数
            result = await crud_experts.update_expert(
                db, non_existent_id, update_data
            )

            # 验证返回None
            assert result is None
            break

    @pytest.mark.asyncio
    async def test_update_expert_duplicate_user_id(self, db_session):
        """测试更新专家失败（user_id重复）"""
        async for db in db_session:
            # 创建两个专家
            user_id1 = uuid.uuid4()
            user_id2 = uuid.uuid4()
            expert1 = await create_test_expert(db, user_id=user_id1, name="专家1")
            await db.commit()
            expert2 = await create_test_expert(db, user_id=user_id2, name="专家2")
            await db.commit()

            # 尝试将expert2的user_id修改为user_id1（冲突）
            update_data = ExpertUpdate(user_id=user_id1)

            # 验证抛出DatabaseIntegrityException
            with pytest.raises(DatabaseIntegrityException) as exc_info:
                await crud_experts.update_expert(db, expert2.id, update_data)
                await db.commit()  # 确保触发约束检查
            
            assert "该用户已绑定到其他专家档案" in str(exc_info.value)
            break

    @pytest.mark.asyncio
    async def test_delete_expert_success(self, db_session):
        """测试成功删除专家（软删除）"""
        async for db in db_session:
            # 创建测试专家
            expert = await create_test_expert(db, is_featured=True)
            await db.commit()

            # 调用CRUD函数
            result = await crud_experts.delete_expert(db, expert.id)

            # 验证返回True
            assert result is True

            # 验证数据库中的记录（软删除：is_active=false）
            db_expert = await crud_experts.get_expert(db, expert.id)
            assert db_expert is not None
            assert db_expert.is_active is False
            break

    @pytest.mark.asyncio
    async def test_delete_expert_not_found(self, db_session):
        """测试删除不存在的专家"""
        async for db in db_session:
            non_existent_id = uuid.uuid4()

            # 调用CRUD函数
            result = await crud_experts.delete_expert(db, non_existent_id)

            # 验证返回False
            assert result is False
            break


# ==================== UserExpertSubscription CRUD测试 ====================

class TestUserExpertSubscriptionCRUD:
    """UserExpertSubscription CRUD函数测试"""

    @pytest.mark.asyncio
    async def test_create_subscription_success(self, db_session):
        """测试成功创建关注记录"""
        async for db in db_session:
            # 创建测试专家
            expert = await create_test_expert(db)
            await db.commit()

            # 准备测试数据
            user_id = uuid.uuid4()

            # 调用CRUD函数
            subscription = await crud_experts.create_subscription(
                db, user_id, expert.id
            )

            # 验证返回值
            assert subscription.id is not None
            assert subscription.user_id == user_id
            assert subscription.expert_id == expert.id
            assert subscription.created_at is not None

            # 验证数据库中的记录
            result = await db.execute(
                select(UserExpertSubscription).where(
                    UserExpertSubscription.id == subscription.id
                )
            )
            db_subscription = result.scalar_one_or_none()
            assert db_subscription is not None
            break

    @pytest.mark.asyncio
    async def test_create_subscription_duplicate(self, db_session):
        """测试创建关注记录失败（重复关注）"""
        async for db in db_session:
            # 创建测试专家和关注记录
            expert = await create_test_expert(db)
            user_id = uuid.uuid4()
            subscription1 = await crud_experts.create_subscription(
                db, user_id, expert.id
            )
            await db.commit()

            # 尝试重复关注
            with pytest.raises(DatabaseIntegrityException) as exc_info:
                await crud_experts.create_subscription(db, user_id, expert.id)
            
            assert "已关注该专家" in str(exc_info.value)
            break

    @pytest.mark.asyncio
    async def test_get_subscription_success(self, db_session):
        """测试成功查询关注记录"""
        async for db in db_session:
            # 创建测试关注记录
            subscription = await create_test_subscription(db)
            await db.commit()

            # 调用CRUD函数
            result = await crud_experts.get_subscription(
                db, subscription.user_id, subscription.expert_id
            )

            # 验证返回值
            assert result is not None
            assert result.id == subscription.id
            assert result.user_id == subscription.user_id
            assert result.expert_id == subscription.expert_id
            break

    @pytest.mark.asyncio
    async def test_get_subscription_not_found(self, db_session):
        """测试查询不存在的关注记录"""
        async for db in db_session:
            user_id = uuid.uuid4()
            expert_id = uuid.uuid4()

            # 调用CRUD函数
            result = await crud_experts.get_subscription(db, user_id, expert_id)

            # 验证返回None
            assert result is None
            break

    @pytest.mark.asyncio
    async def test_get_user_subscriptions(self, db_session):
        """测试获取用户关注列表"""
        async for db in db_session:
            # 创建测试用户和多个专家
            user_id = uuid.uuid4()
            expert1 = await create_test_expert(db)
            expert2 = await create_test_expert(db)
            expert3 = await create_test_expert(db)
            await db.commit()

            # 创建关注记录
            await crud_experts.create_subscription(db, user_id, expert1.id)
            await crud_experts.create_subscription(db, user_id, expert2.id)
            await db.commit()

            # 调用CRUD函数
            results = await crud_experts.get_user_subscriptions(db, user_id)

            # 验证返回值（results是UserExpertSubscription列表）
            assert len(results) == 2
            expert_ids = [r.expert_id for r in results]
            assert expert1.id in expert_ids
            assert expert2.id in expert_ids
            assert expert3.id not in expert_ids
            break

    @pytest.mark.asyncio
    async def test_delete_subscription_success(self, db_session):
        """测试成功删除关注记录"""
        async for db in db_session:
            # 创建测试关注记录
            subscription = await create_test_subscription(db)
            await db.commit()

            # 调用CRUD函数
            result = await crud_experts.delete_subscription(
                db, subscription.user_id, subscription.expert_id
            )

            # 验证返回True
            assert result is True

            # 验证数据库中的记录已删除
            db_subscription = await crud_experts.get_subscription(
                db, subscription.user_id, subscription.expert_id
            )
            assert db_subscription is None
            break

    @pytest.mark.asyncio
    async def test_delete_subscription_not_found(self, db_session):
        """测试删除不存在的关注记录"""
        async for db in db_session:
            user_id = uuid.uuid4()
            expert_id = uuid.uuid4()

            # 调用CRUD函数
            result = await crud_experts.delete_subscription(db, user_id, expert_id)

            # 验证返回False
            assert result is False
            break

    @pytest.mark.asyncio
    async def test_get_subscriptions_by_expert_ids(self, db_session):
        """测试批量查询关注记录"""
        async for db in db_session:
            # 创建测试用户和多个专家
            user_id = uuid.uuid4()
            expert1 = await create_test_expert(db)
            expert2 = await create_test_expert(db)
            expert3 = await create_test_expert(db)
            await db.commit()

            # 创建关注记录（只关注expert1和expert2）
            await crud_experts.create_subscription(db, user_id, expert1.id)
            await crud_experts.create_subscription(db, user_id, expert2.id)
            await db.commit()

            # 调用CRUD函数（查询expert1、expert2、expert3）
            expert_ids = [expert1.id, expert2.id, expert3.id]
            results = await crud_experts.get_subscriptions_by_expert_ids(
                db, user_id, expert_ids
            )

            # 验证返回值（只有expert1和expert2）
            assert len(results) == 2
            subscribed_ids = [r.expert_id for r in results]
            assert expert1.id in subscribed_ids
            assert expert2.id in subscribed_ids
            assert expert3.id not in subscribed_ids
            break


# ==================== LiveSessionExpert CRUD测试 ====================

class TestLiveSessionExpertCRUD:
    """LiveSessionExpert CRUD函数测试"""

    @pytest.mark.asyncio
    async def test_get_session_experts(self, db_session):
        """测试获取场次专家列表"""
        async for db in db_session:
            # 创建测试数据
            session = await create_test_session(db)
            expert1 = await create_test_expert(db)
            expert2 = await create_test_expert(db)
            await db.commit()

            # 手动创建场次专家关联
            session_expert1 = LiveSessionExpert(
                id=uuid.uuid4(),
                session_id=session.id,
                expert_id=expert1.id,
                role=SessionExpertRole.MAIN_SPEAKER,
                sort_order=1
            )
            session_expert2 = LiveSessionExpert(
                id=uuid.uuid4(),
                session_id=session.id,
                expert_id=expert2.id,
                role=SessionExpertRole.GUEST,
                sort_order=2
            )
            db.add(session_expert1)
            db.add(session_expert2)
            await db.commit()

            # 调用CRUD函数（不筛选角色）
            results = await crud_experts.get_session_experts(db, session.id)

            # 验证返回值
            assert len(results) >= 2
            expert_ids = [r.expert_id for r in results]
            assert expert1.id in expert_ids
            assert expert2.id in expert_ids
            break

    @pytest.mark.asyncio
    async def test_get_session_experts_with_role_filter(self, db_session):
        """测试获取场次专家列表（带角色筛选）"""
        async for db in db_session:
            # 创建测试数据
            session = await create_test_session(db)
            expert1 = await create_test_expert(db)
            expert2 = await create_test_expert(db)
            await db.commit()

            # 创建不同角色的场次专家
            session_expert1 = LiveSessionExpert(
                id=uuid.uuid4(),
                session_id=session.id,
                expert_id=expert1.id,
                role=SessionExpertRole.MAIN_SPEAKER,
                sort_order=1
            )
            session_expert2 = LiveSessionExpert(
                id=uuid.uuid4(),
                session_id=session.id,
                expert_id=expert2.id,
                role=SessionExpertRole.GUEST,
                sort_order=2
            )
            db.add(session_expert1)
            db.add(session_expert2)
            await db.commit()

            # 调用CRUD函数（筛选MAIN_SPEAKER）
            results = await crud_experts.get_session_experts(
                db, session.id, role=SessionExpertRole.MAIN_SPEAKER
            )

            # 验证返回值（只有expert1）
            assert len(results) >= 1
            assert results[0].expert_id == expert1.id
            assert results[0].role == SessionExpertRole.MAIN_SPEAKER
            break

    @pytest.mark.asyncio
    async def test_get_expert_sessions(self, db_session):
        """测试获取专家参与的场次列表"""
        async for db in db_session:
            # 创建测试专家和场次
            expert = await create_test_expert(db)
            session1 = await create_test_session(db)
            session2 = await create_test_session(db)
            await db.commit()

            # 创建多个场次专家关联
            session_expert1 = LiveSessionExpert(
                id=uuid.uuid4(),
                session_id=session1.id,
                expert_id=expert.id,
                role=SessionExpertRole.MAIN_SPEAKER,
                sort_order=1
            )
            session_expert2 = LiveSessionExpert(
                id=uuid.uuid4(),
                session_id=session2.id,
                expert_id=expert.id,
                role=SessionExpertRole.GUEST,
                sort_order=1
            )
            db.add(session_expert1)
            db.add(session_expert2)
            await db.commit()

            # 调用CRUD函数
            results, total = await crud_experts.get_expert_sessions(
                db, expert.id, skip=0, limit=10
            )

            # 验证返回值
            assert len(results) == 2
            assert total == 2
            session_ids = [r.session_id for r in results]
            assert session1.id in session_ids
            assert session2.id in session_ids
            break

    @pytest.mark.asyncio
    async def test_get_expert_sessions_with_pagination(self, db_session):
        """测试获取专家参与的场次列表（分页）"""
        async for db in db_session:
            # 创建测试专家
            expert = await create_test_expert(db)
            await db.commit()

            # 创建5个场次和场次专家关联
            for i in range(5):
                session = await create_test_session(db)
                session_expert = LiveSessionExpert(
                    id=uuid.uuid4(),
                    session_id=session.id,
                    expert_id=expert.id,
                    role=SessionExpertRole.MAIN_SPEAKER,
                    sort_order=i
                )
                db.add(session_expert)
            await db.commit()

            # 调用CRUD函数（分页：skip=1, limit=2）
            results, total = await crud_experts.get_expert_sessions(
                db, expert.id, skip=1, limit=2
            )

            # 验证返回值
            assert len(results) == 2
            assert total == 5
            break

    @pytest.mark.asyncio
    async def test_set_session_experts_success(self, db_session):
        """测试成功设置场次专家列表"""
        async for db in db_session:
            # 创建测试专家和场次
            expert1 = await create_test_expert(db)
            expert2 = await create_test_expert(db)
            session = await create_test_session(db)
            await db.commit()

            # 准备测试数据
            expert_data_list = [
                {
                    "expert_id": expert1.id,
                    "role": SessionExpertRole.MAIN_SPEAKER,
                    "sort_order": 1
                },
                {
                    "expert_id": expert2.id,
                    "role": SessionExpertRole.GUEST,
                    "sort_order": 2
                }
            ]

            # 调用CRUD函数
            results = await crud_experts.set_session_experts(
                db, session.id, expert_data_list
            )

            # 验证返回值
            assert len(results) == 2
            assert results[0].expert_id == expert1.id
            assert results[0].role == SessionExpertRole.MAIN_SPEAKER
            assert results[1].expert_id == expert2.id
            assert results[1].role == SessionExpertRole.GUEST

            # 验证数据库中的记录
            db_results = await crud_experts.get_session_experts(db, session.id)
            assert len(db_results) == 2
            break

    @pytest.mark.asyncio
    async def test_set_session_experts_duplicate(self, db_session):
        """测试设置场次专家列表失败（唯一性冲突）"""
        async for db in db_session:
            # 创建测试专家
            expert = await create_test_expert(db)
            await db.commit()

            # 准备测试数据（相同expert_id和role）
            session_id = uuid.uuid4()
            expert_data_list = [
                {
                    "expert_id": expert.id,
                    "role": SessionExpertRole.MAIN_SPEAKER,
                    "sort_order": 1
                },
                {
                    "expert_id": expert.id,
                    "role": SessionExpertRole.MAIN_SPEAKER,  # 重复的角色
                    "sort_order": 2
                }
            ]

            # 调用CRUD函数（应该抛出IntegrityError）
            with pytest.raises((IntegrityError, DatabaseIntegrityException)):
                await crud_experts.set_session_experts(db, session_id, expert_data_list)
            break


# ==================== 增量测试：is_active 与软删除 ====================

@pytest.mark.asyncio
async def test_create_expert_is_active_default_true(db_session):
    """增量：创建专家时未传 is_active，默认为 True"""
    async for db in db_session:
        expert_data = ExpertCreate(
            name=fake.name(),
            title="主任医师",
            hospital=fake.company(),
            is_featured=False,
        )
        expert = await crud_experts.create_expert(db, expert_data)
        assert expert.is_active is True
        break


@pytest.mark.asyncio
async def test_create_expert_is_active_explicit_false(db_session):
    """增量：创建专家时显式传入 is_active=False"""
    async for db in db_session:
        expert_data = ExpertCreate(
            name=fake.name(),
            title="主任医师",
            hospital=fake.company(),
            is_featured=False,
            is_active=False,
        )
        expert = await crud_experts.create_expert(db, expert_data)
        assert expert.is_active is False
        break


@pytest.mark.asyncio
async def test_get_featured_experts_excludes_inactive(db_session):
    """增量：get_featured_experts 不包含 is_active=False 的专家"""
    async for db in db_session:
        featured_active = await create_test_expert(db, is_featured=True, is_active=True, sort_order=0)
        featured_inactive = await create_test_expert(db, is_featured=True, is_active=False, sort_order=0)
        results = await crud_experts.get_featured_experts(db, limit=50)
        ids = [r.id for r in results]
        assert featured_active.id in ids
        assert featured_inactive.id not in ids
        break


@pytest.mark.asyncio
async def test_get_experts_multi_and_total_filter_by_is_active(db_session):
    """增量：get_experts_multi_and_total 支持 is_active 筛选"""
    async for db in db_session:
        import time
        suffix = str(int(time.time() * 1000) % 100000)
        active_one = await create_test_expert(db, name=f"Active{suffix}", is_active=True)
        inactive_one = await create_test_expert(db, name=f"Inactive{suffix}", is_active=False)
        experts_true, total_true = await crud_experts.get_experts_multi_and_total(
            db, skip=0, limit=100, name=f"Active{suffix}", is_active=True
        )
        experts_false, total_false = await crud_experts.get_experts_multi_and_total(
            db, skip=0, limit=100, name=f"Inactive{suffix}", is_active=False
        )
        assert any(e.id == active_one.id for e in experts_true)
        assert not any(e.id == inactive_one.id for e in experts_true)
        assert any(e.id == inactive_one.id for e in experts_false)
        assert not any(e.id == active_one.id for e in experts_false)
        break


@pytest.mark.asyncio
async def test_update_expert_is_active(db_session):
    """增量：更新专家可设置 is_active"""
    async for db in db_session:
        expert = await create_test_expert(db, is_active=True)
        await db.commit()
        updated = await crud_experts.update_expert(
            db, expert.id, ExpertUpdate(is_active=False)
        )
        assert updated is not None
        assert updated.is_active is False
        break


@pytest.mark.asyncio
async def test_delete_expert_soft_delete_sets_is_active_false(db_session):
    """增量：delete_expert 软删除为设置 is_active=False"""
    async for db in db_session:
        expert = await create_test_expert(db, is_active=True)
        await db.commit()
        result = await crud_experts.delete_expert(db, expert.id)
        assert result is True
        db_expert = await crud_experts.get_expert(db, expert.id)
        assert db_expert is not None
        assert db_expert.is_active is False
        break
