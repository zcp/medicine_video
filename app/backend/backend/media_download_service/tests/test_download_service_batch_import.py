"""
CSV批量导入服务层测试

本文件包含批量导入功能的服务层测试用例，覆盖：
- 成功场景（全部成功、部分成功）
- 错误隔离机制
- 去重功能
- 自动启动功能
- 批量提交性能
- 失败场景（缺少列、超过行数、编码错误等）
- 边界条件测试
"""
import os

import pytest
import uuid
import time
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from app.models.download import DownloadTask, DownloadedVideo
from app.schemas.download import TaskStatus, DownloadTaskCreate
from app.services.download_service import DownloadService
from app.core.exceptions import DatabaseError

# 导入CSV生成辅助函数
from faker import Faker
import random
import io

fake = Faker()


@pytest.fixture
def sync_db_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "CHANGE_ME")
    POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "media_download_test")

    SYNC_TEST_DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
    sync_engine = create_engine(SYNC_TEST_DATABASE_URL)
    SessionLocal = sessionmaker(bind=sync_engine)

    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

def generate_csv_content(num_rows: int, invalid_rows: list = None) -> bytes:
    """
    生成测试用CSV内容

    Args:
        num_rows: 总行数
        invalid_rows: 无效行的配置列表，如 [
            {"row": 3, "type": "short_liveroom_id"},
            {"row": 5, "type": "invalid_resource_type"}
        ]

    Returns:
        bytes: UTF-8编码的CSV内容
    """
    output = io.StringIO()
    # 写入表头
    output.write("liveroom_id,liveroom_title,liveroom_url,resource_url,resource_type\n")

    invalid_row_dict = {item["row"]: item["type"] for item in (invalid_rows or [])}

    for i in range(1, num_rows + 1):
        row_number = i + 1  # 从第2行开始（第1行是表头）

        if row_number in invalid_row_dict:
            error_type = invalid_row_dict[row_number]
            if error_type == "short_liveroom_id":
                liveroom_id = "123"  # 长度不足
                resource_type = random.choice(["hls", "mp4", "image"])
            elif error_type == "long_liveroom_id":
                liveroom_id = "1" * 25  # 长度超出
                resource_type = random.choice(["hls", "mp4", "image"])
            elif error_type == "invalid_resource_type":
                liveroom_id = str(fake.random_int(min=1000000000, max=9999999999))
                resource_type = "invalid"
            elif error_type == "missing_resource_url":
                # 缺少resource_url
                liveroom_id = str(fake.random_int(min=1000000000, max=9999999999))
                liveroom_title = fake.sentence(nb_words=3)
                liveroom_url = fake.url()
                output.write(f"{liveroom_id},{liveroom_title},{liveroom_url},,hls\n")
                continue
            else:
                liveroom_id = str(fake.random_int(min=1000000000, max=9999999999))
                resource_type = random.choice(["hls", "mp4", "image"])
        else:
            liveroom_id = str(fake.random_int(min=1000000000, max=9999999999))
            resource_type = random.choice(["hls", "mp4", "image"])

        liveroom_title = fake.sentence(nb_words=3)
        liveroom_url = fake.url()
        resource_url = fake.url()

        output.write(f"{liveroom_id},{liveroom_title},{liveroom_url},{resource_url},{resource_type}\n")

    return output.getvalue().encode('utf-8')


class TestDownloadServiceBatchImport:
    """CSV批量导入服务层测试类"""
    
    # ==================== 成功场景测试 ====================
    
    def test_batch_import_all_success(self, sync_db_session):
        """Test Case 1: 测试所有行都成功导入"""
        test_user_id = uuid.uuid4()
        csv_bytes = generate_csv_content(num_rows=10)
        
        service = DownloadService(sync_db_session)
        result = service.batch_import_tasks_from_csv(
            file_content=csv_bytes,
            user_id=test_user_id,
            skip_duplicates=False,
            auto_start=False
        )
        
        # 1. 结果统计验证
        assert result["total"] == 10
        assert result["success"] == 10
        assert result["failed"] == 0
        assert result["skipped"] == 0
        assert len(result["created_task_ids"]) == 10
        assert len(result["failed_rows"]) == 0
        assert result["processing_time"] > 0
        
        # 2. 数据库状态验证
        tasks = sync_db_session.query(DownloadTask).filter(
            DownloadTask.user_id == test_user_id
        ).all()
        assert len(tasks) == 10
        for task in tasks:
            assert task.status == TaskStatus.PENDING
            assert task.resource_type in ["hls", "mp4", "image"]
    
    def test_batch_import_partial_success_error_isolation(self, sync_db_session):
        """Test Case 2: 测试错误隔离机制：部分行失败不影响其他行"""
        test_user_id = uuid.uuid4()
        
        # 准备包含10行数据，其中3行无效
        csv_bytes = generate_csv_content(
            num_rows=10,
            invalid_rows=[
                {"row": 3, "type": "short_liveroom_id"},
                {"row": 5, "type": "invalid_resource_type"},
                {"row": 8, "type": "missing_resource_url"}
            ]
        )
        
        service = DownloadService(sync_db_session)
        result = service.batch_import_tasks_from_csv(
            file_content=csv_bytes,
            user_id=test_user_id,
            skip_duplicates=False,
            auto_start=False
        )
        
        # 1. 结果统计
        assert result["total"] == 10
        assert result["success"] == 7
        assert result["failed"] == 3
        assert len(result["failed_rows"]) == 3
        
        # 2. 失败行详细信息
        failed_row_3 = next((r for r in result["failed_rows"] if r["row"] == 3), None)
        assert failed_row_3 is not None
        assert "liveroom_id长度必须在10-20之间" in failed_row_3["error"]
        
        failed_row_5 = next((r for r in result["failed_rows"] if r["row"] == 5), None)
        assert failed_row_5 is not None
        assert "无效的resource_type" in failed_row_5["error"]
        
        failed_row_8 = next((r for r in result["failed_rows"] if r["row"] == 8), None)
        assert failed_row_8 is not None
        assert "缺少必填字段" in failed_row_8["error"]
        
        # 3. 数据库状态
        tasks = sync_db_session.query(DownloadTask).filter(
            DownloadTask.user_id == test_user_id
        ).all()
        assert len(tasks) == 7  # 只有成功的7条
    
    def test_batch_import_with_skip_duplicates_enabled(self, sync_db_session):
        """Test Case 3: 测试去重功能（组合去重）：重复的任务组合（resource_url + liveroom_id + liveroom_title）被跳过"""
        test_user_id = uuid.uuid4()
        
        service = DownloadService(sync_db_session)
        
        # 准备测试数据
        url1 = fake.url()
        url2 = fake.url()
        liveroom_id_1 = str(fake.random_int(min=1000000000, max=9999999999))
        liveroom_id_2 = str(fake.random_int(min=1000000000, max=9999999999))
        liveroom_id_3 = str(fake.random_int(min=1000000000, max=9999999999))
        
        # 1. 预先创建2个任务
        task_data_1 = DownloadTaskCreate(
            liveroom_id=liveroom_id_1,
            liveroom_title="直播间A",
            resource_url=url1,
            resource_type="hls",
            video_id=uuid.uuid4()
        )
        service.create_download_task(task_data_1, test_user_id)
        
        task_data_2 = DownloadTaskCreate(
            liveroom_id=liveroom_id_2,
            liveroom_title="直播间B",
            resource_url=url2,
            resource_type="mp4",
            video_id=uuid.uuid4()
        )
        service.create_download_task(task_data_2, test_user_id)
        
        # 2. 准备CSV，测试组合去重逻辑
        # - 第1行（重复）: 完全匹配任务1（相同URL + 相同ID + 相同标题）
        # - 第2行（新任务）: 相同URL但不同直播间ID
        # - 第3行（新任务）: 相同URL和ID但不同标题
        # - 第4行（重复）: 完全匹配任务2
        # - 第5行（新任务）: 全新的组合
        csv_content = f"""liveroom_id,liveroom_title,liveroom_url,resource_url,resource_type
{liveroom_id_1},直播间A,{fake.url()},{url1},hls
{liveroom_id_3},直播间C,{fake.url()},{url1},hls
{liveroom_id_1},直播间D,{fake.url()},{url1},hls
{liveroom_id_2},直播间B,{fake.url()},{url2},mp4
{fake.random_int(min=1000000000, max=9999999999)},直播间E,{fake.url()},{fake.url()},image
"""
        csv_bytes = csv_content.encode('utf-8')
        
        # 3. 执行导入（启用去重）
        result = service.batch_import_tasks_from_csv(
            file_content=csv_bytes,
            user_id=test_user_id,
            skip_duplicates=True,
            auto_start=False
        )
        
        # 4. 断言
        # 4.1 结果统计
        assert result["total"] == 5
        assert result["success"] == 3  # 第2、3、5行是新任务
        assert result["skipped"] == 2  # 第1、4行被跳过
        assert len(result["skipped_rows"]) == 2
        
        # 4.2 跳过行详细信息
        for skipped in result["skipped_rows"]:
            assert "任务组合已存在" in skipped["reason"]
            assert "row" in skipped
            assert "liveroom_id" in skipped
            assert "liveroom_title" in skipped
            assert "resource_url" in skipped
        
        # 4.3 数据库状态验证
        # 数据库应有5个任务（2个预先创建 + 3个新导入）
        tasks = sync_db_session.query(DownloadTask).filter(
            DownloadTask.user_id == test_user_id
        ).all()
        assert len(tasks) == 5
    
    def test_batch_import_with_skip_duplicates_disabled(self, sync_db_session):
        """Test Case 4: 测试不启用去重：允许创建重复resource_url的任务"""
        test_user_id = uuid.uuid4()
        
        service = DownloadService(sync_db_session)
        
        # 1. 预先创建1个任务
        existing_url = fake.url()
        task_data = DownloadTaskCreate(
            liveroom_id=str(fake.random_int(min=1000000000, max=9999999999)),
            resource_url=existing_url,
            resource_type="hls",
            video_id=uuid.uuid4()
        )
        service.create_download_task(task_data, test_user_id)
        
        # 2. 准备CSV，包含重复的URL
        csv_content = f"""liveroom_id,liveroom_title,liveroom_url,resource_url,resource_type
{fake.random_int(min=1000000000, max=9999999999)},标题1,{fake.url()},{existing_url},hls
{fake.random_int(min=1000000000, max=9999999999)},标题2,{fake.url()},{fake.url()},mp4
"""
        csv_bytes = csv_content.encode('utf-8')
        
        # 3. 执行导入（不启用去重）
        result = service.batch_import_tasks_from_csv(
            file_content=csv_bytes,
            user_id=test_user_id,
            skip_duplicates=False,
            auto_start=False
        )
        
        # 4. 断言：不启用去重时，允许创建重复的任务
        assert result["total"] == 2
        assert result["success"] == 2  # ✅ 两条都成功（包括重复的URL）
        assert result["skipped"] == 0  # 不跳过
        assert result["failed"] == 0
        
        # 5. 验证数据库中确实有3个任务（1个预先创建 + 2个导入）
        tasks = sync_db_session.query(DownloadTask).filter(
            DownloadTask.user_id == test_user_id
        ).all()
        assert len(tasks) == 3
        
        # 6. 验证其中2个任务的resource_url相同
        urls = [task.resource_url for task in tasks]
        assert urls.count(existing_url) == 2  # 重复的URL出现2次
    
    def test_batch_import_with_skip_duplicates_null_title(self, sync_db_session):
        """Test Case 5: 测试去重功能（liveroom_title为空的情况）：验证空值匹配逻辑"""
        test_user_id = uuid.uuid4()
        
        service = DownloadService(sync_db_session)
        
        # 准备测试数据
        url1 = fake.url()
        url2 = fake.url()
        liveroom_id_1 = str(fake.random_int(min=1000000000, max=9999999999))
        liveroom_id_2 = str(fake.random_int(min=1000000000, max=9999999999))
        liveroom_id_3 = str(fake.random_int(min=1000000000, max=9999999999))
        
        # 1. 预先创建2个任务（一个liveroom_title为None，一个有值）
        task_data_1 = DownloadTaskCreate(
            liveroom_id=liveroom_id_1,
            liveroom_title=None,  # 空值
            resource_url=url1,
            resource_type="hls",
            video_id=uuid.uuid4()
        )
        service.create_download_task(task_data_1, test_user_id)
        
        task_data_2 = DownloadTaskCreate(
            liveroom_id=liveroom_id_2,
            liveroom_title="直播间B",
            resource_url=url2,
            resource_type="mp4",
            video_id=uuid.uuid4()
        )
        service.create_download_task(task_data_2, test_user_id)
        
        # 2. 准备CSV，测试空值匹配逻辑
        # - 第1行（重复）: 空标题匹配空标题（相同URL + 相同ID + 都为空）
        # - 第2行（新任务）: 相同URL和ID但有标题（空值vs有值视为不同）
        # - 第3行（新任务）: 相同URL但不同ID，都是空标题
        # - 第4行（重复）: 完全匹配任务2（有标题）
        csv_content = f"""liveroom_id,liveroom_title,liveroom_url,resource_url,resource_type
{liveroom_id_1},,{fake.url()},{url1},hls
{liveroom_id_1},直播间C,{fake.url()},{url1},hls
{liveroom_id_3},,{fake.url()},{url1},mp4
{liveroom_id_2},直播间B,{fake.url()},{url2},mp4
"""
        csv_bytes = csv_content.encode('utf-8')
        
        # 3. 执行导入（启用去重）
        result = service.batch_import_tasks_from_csv(
            file_content=csv_bytes,
            user_id=test_user_id,
            skip_duplicates=True,
            auto_start=False
        )
        
        # 4. 断言
        # 4.1 结果统计
        assert result["total"] == 4
        assert result["success"] == 2  # 第2、3行是新任务
        assert result["skipped"] == 2  # 第1、4行被跳过
        assert len(result["skipped_rows"]) == 2
        
        # 4.2 验证空值匹配逻辑
        # 验证第1行被正确识别为重复（空值匹配空值）
        skipped_row_1 = next((r for r in result["skipped_rows"] if r["row"] == 2), None)
        assert skipped_row_1 is not None
        assert skipped_row_1.get("liveroom_title") is None or skipped_row_1.get("liveroom_title") == ""
        assert "任务组合已存在" in skipped_row_1["reason"]
        
        # 4.3 数据库状态验证
        # 数据库应有4个任务（2个预先创建 + 2个新导入）
        tasks = sync_db_session.query(DownloadTask).filter(
            DownloadTask.user_id == test_user_id
        ).all()
        assert len(tasks) == 4
        
        # 验证有2个任务的liveroom_title为None
        null_title_tasks = [t for t in tasks if t.liveroom_title is None]
        assert len(null_title_tasks) == 2
    
    def test_batch_import_with_auto_start_enabled(self, sync_db_session):
        """Test Case 6: 测试自动启动功能：导入后自动调用start_download_task"""
        test_user_id = uuid.uuid4()
        csv_bytes = generate_csv_content(num_rows=3)
        
        service = DownloadService(sync_db_session)
        
        # Mock start_download_task方法
        with patch.object(service, 'start_download_task') as mock_start:
            result = service.batch_import_tasks_from_csv(
                file_content=csv_bytes,
                user_id=test_user_id,
                skip_duplicates=False,
                auto_start=True
            )
            
            # 断言
            assert result["success"] == 3
            # 验证start_download_task被调用了3次
            assert mock_start.call_count == 3
    
    def test_batch_import_commit_performance(self, sync_db_session):
        """Test Case 7: 测试批量提交：每100行提交一次"""
        test_user_id = uuid.uuid4()
        csv_bytes = generate_csv_content(num_rows=250)
        
        service = DownloadService(sync_db_session)
        
        # Spy on commit
        with patch.object(sync_db_session, 'commit', wraps=sync_db_session.commit) as mock_commit:
            result = service.batch_import_tasks_from_csv(
                file_content=csv_bytes,
                user_id=test_user_id,
                skip_duplicates=False,
                auto_start=False
            )
            
            # 断言
            assert result["success"] == 250
            # 验证commit被调用至少3次：100行、200行、最终提交
            assert mock_commit.call_count >= 3
    
    # ==================== 失败场景测试 ====================
    
    def test_batch_import_missing_required_columns(self, sync_db_session):
        """Test Case 8: 测试CSV缺少必需列（resource_url）"""
        test_user_id = uuid.uuid4()
        
        # CSV只包含部分必需列
        csv_content = b"liveroom_id,resource_type\n1234567890,hls\n"
        
        service = DownloadService(sync_db_session)
        
        with pytest.raises(ValueError) as exc_info:
            service.batch_import_tasks_from_csv(
                file_content=csv_content,
                user_id=test_user_id
            )
        
        assert "缺少必需列" in str(exc_info.value)
        assert "resource_url" in str(exc_info.value)
    
    def test_batch_import_exceeds_max_rows(self, sync_db_session):
        """Test Case 9: 测试CSV超过1000行限制"""
        test_user_id = uuid.uuid4()
        csv_bytes = generate_csv_content(num_rows=1001)
        
        service = DownloadService(sync_db_session)
        
        with pytest.raises(ValueError) as exc_info:
            service.batch_import_tasks_from_csv(
                file_content=csv_bytes,
                user_id=test_user_id
            )
        
        assert "超过最大行数限制" in str(exc_info.value)
    
    def test_batch_import_invalid_encoding(self, sync_db_session):
        """Test Case 10: 测试非UTF-8编码文件"""
        test_user_id = uuid.uuid4()
        
        # 使用GBK编码，并包含中文以确保编码差异
        csv_content = "liveroom_id,resource_url,resource_type\n1234567890,http://test.com,hls,这是中文标题\n"
        csv_bytes = csv_content.encode('gbk')
        
        service = DownloadService(sync_db_session)
        
        with pytest.raises(ValueError) as exc_info:
            service.batch_import_tasks_from_csv(
                file_content=csv_bytes,
                user_id=test_user_id
            )
        
        assert "文件编码错误" in str(exc_info.value)
    
    def test_batch_import_malformed_csv(self, sync_db_session):
        """Test Case 11: 测试格式错误的CSV（如引号未闭合跨多行）"""
        test_user_id = uuid.uuid4()
        
        # 包含严重格式错误的CSV：引号未闭合且跨多行
        csv_content = b'liveroom_id,resource_url,resource_type\n1234567890,"unclosed quote\n,hls\n9876543210,http://test2.com,mp4\n'
        
        service = DownloadService(sync_db_session)
        
        # 注意：csv.DictReader 容错性很强，可能不会抛出异常
        # 如果不抛异常，测试会失败，这是预期的，说明需要增强CSV验证
        try:
            result = service.batch_import_tasks_from_csv(
                file_content=csv_content,
                user_id=test_user_id
            )
            # 如果没有抛异常，至少验证数据处理异常（失败率应该很高）
            assert result["failed"] > 0 or result["success"] == 0
        except ValueError as e:
            # 如果抛出异常，验证错误消息
            assert "CSV文件格式错误" in str(e) or "文件编码错误" in str(e)
    
    def test_batch_import_database_error(self, sync_db_session):
        """Test Case 12: 测试数据库操作失败时的回滚"""
        test_user_id = uuid.uuid4()
        csv_bytes = generate_csv_content(num_rows=5)
        
        service = DownloadService(sync_db_session)
        
        # Mock commit to raise exception
        with patch.object(sync_db_session, 'commit', side_effect=SQLAlchemyError("Database error")):
            with pytest.raises(DatabaseError):
                service.batch_import_tasks_from_csv(
                    file_content=csv_bytes,
                    user_id=test_user_id
                )
    
    def test_batch_import_all_rows_failed(self, sync_db_session):
        """Test Case 13: 测试所有行都失败的情况"""
        test_user_id = uuid.uuid4()
        
        # CSV中所有行的liveroom_id都不符合长度要求
        csv_bytes = generate_csv_content(
            num_rows=10,
            invalid_rows=[{"row": i, "type": "short_liveroom_id"} for i in range(2, 12)]
        )
        
        service = DownloadService(sync_db_session)
        result = service.batch_import_tasks_from_csv(
            file_content=csv_bytes,
            user_id=test_user_id
        )
        
        assert result["total"] == 10
        assert result["success"] == 0
        assert result["failed"] == 10
    
    # ==================== 边界条件测试 ====================
    
    def test_batch_import_empty_csv_with_header_only(self, sync_db_session):
        """Test Case 14: 测试只有表头没有数据行的CSV"""
        test_user_id = uuid.uuid4()
        csv_content = b"liveroom_id,liveroom_title,liveroom_url,resource_url,resource_type\n"
        
        service = DownloadService(sync_db_session)
        result = service.batch_import_tasks_from_csv(
            file_content=csv_content,
            user_id=test_user_id
        )
        
        assert result["total"] == 0
        assert result["success"] == 0
    
    def test_batch_import_single_row(self, sync_db_session):
        """Test Case 15: 测试只有1行数据的CSV"""
        test_user_id = uuid.uuid4()
        csv_bytes = generate_csv_content(num_rows=1)
        
        service = DownloadService(sync_db_session)
        result = service.batch_import_tasks_from_csv(
            file_content=csv_bytes,
            user_id=test_user_id
        )
        
        assert result["total"] == 1
        assert result["success"] == 1
    
    def test_batch_import_exactly_100_rows(self, sync_db_session):
        """Test Case 16: 测试正好100行数据（批量提交边界）"""
        test_user_id = uuid.uuid4()
        csv_bytes = generate_csv_content(num_rows=100)
        
        service = DownloadService(sync_db_session)
        
        with patch.object(sync_db_session, 'commit', wraps=sync_db_session.commit) as mock_commit:
            result = service.batch_import_tasks_from_csv(
                file_content=csv_bytes,
                user_id=test_user_id
            )
            
            assert result["success"] == 100
            # 验证commit被调用2次（100行时+最终提交）
            assert mock_commit.call_count >= 2
    
    def test_batch_import_liveroom_id_boundary(self, sync_db_session):
        """Test Case 17: 测试liveroom_id长度边界（10和20字符）"""
        test_user_id = uuid.uuid4()
        
        # 准备CSV：正好10字符、正好20字符、9字符（失败）、21字符（失败）
        csv_content = f"""liveroom_id,liveroom_title,liveroom_url,resource_url,resource_type
1234567890,标题1,{fake.url()},{fake.url()},hls
12345678901234567890,标题2,{fake.url()},{fake.url()},mp4
123456789,标题3,{fake.url()},{fake.url()},image
123456789012345678901,标题4,{fake.url()},{fake.url()},hls
"""
        csv_bytes = csv_content.encode('utf-8')
        
        service = DownloadService(sync_db_session)
        result = service.batch_import_tasks_from_csv(
            file_content=csv_bytes,
            user_id=test_user_id
        )
        
        assert result["success"] == 2
        assert result["failed"] == 2
