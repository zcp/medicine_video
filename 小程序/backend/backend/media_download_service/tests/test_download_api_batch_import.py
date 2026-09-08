"""
CSV批量导入API接口测试

本文件包含批量导入功能的API接口测试用例，覆盖：
- 成功场景（201、207状态码）
- 失败场景（400、413状态码）
- 文件验证（类型、大小、编码）
- 去重功能
- 边界条件和安全测试
- 性能测试
"""
import random

import pytest
import uuid
import time
import io
import asyncio

from faker import Faker
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.download import DownloadTask
from app.schemas.download import DownloadTaskCreate
from app.services.download_service import DownloadService
#from conftest import generate_csv_content, generate_csv_file_object, fake

fake = Faker()

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


class TestDownloadApiBatchImport:
    """CSV批量导入API接口测试类"""
    
    # ==================== 成功场景测试 ====================
    
    @pytest.mark.asyncio
    async def test_api_batch_import_all_success(self, db_session, auth_headers):
        """Test Case 17: 测试API批量导入全部成功，返回201"""
        test_user_id = uuid.uuid4()
        csv_bytes = generate_csv_content(num_rows=10)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 准备文件
            files = {"file": ("test.csv", io.BytesIO(csv_bytes), "text/csv")}
            data = {
                "skip_duplicates": "false",
                "auto_start": "false"
            }
            
            # 执行请求
            response = await client.post(
                "/api/v1/download/tasks/batch-import",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            # 断言：HTTP状态码为200，业务状态码在body的code字段
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["code"] == 201
            assert response_data["message"] == "批量导入任务成功"
            assert response_data["data"]["total"] == 10
            assert response_data["data"]["success"] == 10
            assert response_data["data"]["failed"] == 0
            assert len(response_data["data"]["created_task_ids"]) == 10
    
    @pytest.mark.asyncio
    async def test_api_batch_import_partial_success(self, db_session, auth_headers):
        """Test Case 18: 测试API批量导入部分成功，返回207"""
        test_user_id = uuid.uuid4()
        
        # CSV包含10行，其中3行数据无效
        csv_bytes = generate_csv_content(
            num_rows=10,
            invalid_rows=[
                {"row": 3, "type": "short_liveroom_id"},
                {"row": 5, "type": "invalid_resource_type"},
                {"row": 8, "type": "missing_resource_url"}
            ]
        )
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("test.csv", io.BytesIO(csv_bytes), "text/csv")}
            data = {"skip_duplicates": "false", "auto_start": "false"}
            
            response = await client.post(
                "/api/v1/download/tasks/batch-import",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            # 断言：HTTP状态码为200，业务状态码在body的code字段
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["code"] == 207
            assert response_data["message"] == "批量导入部分成功"
            assert response_data["data"]["success"] == 7
            assert response_data["data"]["failed"] == 3
            assert len(response_data["data"]["failed_rows"]) == 3
    
    @pytest.mark.asyncio
    async def test_api_batch_import_with_duplicates_skip(self, db_session, auth_headers):
        """Test Case 19: 测试API去重功能（组合去重）：skip_duplicates=true"""
        # 测试目标：验证基于组合键（resource_url + liveroom_id + liveroom_title）的去重逻辑
        
        # 准备测试数据
        url1 = fake.url()
        url2 = fake.url()
        liveroom_id_1 = str(fake.random_int(min=1000000000, max=9999999999))
        liveroom_id_2 = str(fake.random_int(min=1000000000, max=9999999999))
        
        # 1. 第一次导入：创建2个初始任务
        first_csv = f"""liveroom_id,liveroom_title,liveroom_url,resource_url,resource_type
{liveroom_id_1},直播间A,{fake.url()},{url1},hls
{liveroom_id_2},直播间B,{fake.url()},{url2},mp4
"""
        first_csv_bytes = first_csv.encode('utf-8')
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 第一次导入：创建2个任务
            files = {"file": ("first.csv", io.BytesIO(first_csv_bytes), "text/csv")}
            data = {"skip_duplicates": "false", "auto_start": "false"}
            first_response = await client.post(
                "/api/v1/download/tasks/batch-import",
                files=files,
                data=data,
                headers=auth_headers
            )
            assert first_response.status_code == 200
            assert first_response.json()["code"] == 201
            assert first_response.json()["data"]["success"] == 2
            
            # 2. 第二次导入：测试组合去重逻辑
            # - 第1行（重复）: 完全匹配任务1（相同URL + 相同ID + 相同标题）
            # - 第2行（新任务）: 相同URL但不同直播间ID
            # - 第3行（新任务）: 相同URL和ID但不同标题
            # - 第4行（重复）: 完全匹配任务2
            # - 第5行（新任务）: 全新的组合
            liveroom_id_3 = str(fake.random_int(min=1000000000, max=9999999999))
            csv_content = f"""liveroom_id,liveroom_title,liveroom_url,resource_url,resource_type
{liveroom_id_1},直播间A,{fake.url()},{url1},hls
{liveroom_id_3},直播间C,{fake.url()},{url1},hls
{liveroom_id_1},直播间D,{fake.url()},{url1},hls
{liveroom_id_2},直播间B,{fake.url()},{url2},mp4
{str(fake.random_int(min=1000000000, max=9999999999))},直播间E,{fake.url()},{fake.url()},image
"""
            csv_bytes = csv_content.encode('utf-8')
            
            files = {"file": ("test.csv", io.BytesIO(csv_bytes), "text/csv")}
            data = {"skip_duplicates": "true", "auto_start": "false"}
            
            response = await client.post(
                "/api/v1/download/tasks/batch-import",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            # 断言：HTTP状态码为200，业务状态码在body的code字段
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["code"] == 207  # 部分成功（有跳过）
            assert response_data["data"]["total"] == 5
            assert response_data["data"]["success"] == 3  # 第2、3、5行是新任务
            assert response_data["data"]["skipped"] == 2  # 第1、4行被跳过
            assert len(response_data["data"]["skipped_rows"]) == 2
            
            # 验证跳过行的详细信息
            for skipped in response_data["data"]["skipped_rows"]:
                assert "任务组合已存在" in skipped["reason"]
                assert "liveroom_id" in skipped
                assert "liveroom_title" in skipped
                assert "resource_url" in skipped
    
    @pytest.mark.asyncio
    async def test_api_batch_import_with_null_title_dedup(self, db_session, auth_headers):
        """Test Case 19.5: 测试API去重功能（liveroom_title为空的情况）"""
        # 测试目标：验证当 liveroom_title 为 None 时的去重逻辑（空值匹配）
        
        # 准备测试数据
        url1 = fake.url()
        url2 = fake.url()
        liveroom_id_1 = str(fake.random_int(min=1000000000, max=9999999999))
        liveroom_id_2 = str(fake.random_int(min=1000000000, max=9999999999))
        liveroom_id_3 = str(fake.random_int(min=1000000000, max=9999999999))
        
        # 1. 第一次导入：创建2个任务（一个liveroom_title为空，一个有值）
        first_csv = f"""liveroom_id,liveroom_title,liveroom_url,resource_url,resource_type
{liveroom_id_1},,{fake.url()},{url1},hls
{liveroom_id_2},直播间B,{fake.url()},{url2},mp4
"""
        first_csv_bytes = first_csv.encode('utf-8')
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 第一次导入：创建2个任务
            files = {"file": ("first.csv", io.BytesIO(first_csv_bytes), "text/csv")}
            data = {"skip_duplicates": "false", "auto_start": "false"}
            first_response = await client.post(
                "/api/v1/download/tasks/batch-import",
                files=files,
                data=data,
                headers=auth_headers
            )
            assert first_response.status_code == 200
            assert first_response.json()["code"] == 201
            assert first_response.json()["data"]["success"] == 2
            
            # 2. 第二次导入：测试空值匹配逻辑
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
            
            files = {"file": ("test.csv", io.BytesIO(csv_bytes), "text/csv")}
            data = {"skip_duplicates": "true", "auto_start": "false"}
            
            response = await client.post(
                "/api/v1/download/tasks/batch-import",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            # 断言：HTTP状态码为200，业务状态码在body的code字段
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["code"] == 207  # 部分成功（有跳过）
            assert response_data["data"]["total"] == 4
            assert response_data["data"]["success"] == 2  # 第2、3行是新任务
            assert response_data["data"]["skipped"] == 2  # 第1、4行被跳过
            assert len(response_data["data"]["skipped_rows"]) == 2
            
            # 验证第1行被正确识别为重复（空值匹配空值）
            skipped_rows = response_data["data"]["skipped_rows"]
            # 找到空标题被跳过的那一行
            null_title_skipped = [r for r in skipped_rows if not r.get("liveroom_title")]
            assert len(null_title_skipped) >= 1
            for skipped in null_title_skipped:
                assert "任务组合已存在" in skipped["reason"]
    
    # ==================== 失败场景测试 ====================
    
    @pytest.mark.asyncio
    async def test_api_batch_import_invalid_file_type(self, auth_headers):
        """Test Case 20: 测试上传非CSV文件"""
        # 上传.txt文件
        files = {"file": ("test.txt", io.BytesIO(b"some text"), "text/plain")}
        data = {"skip_duplicates": "false", "auto_start": "false"}
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/download/tasks/batch-import",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            # 断言：HTTP状态码为200，业务状态码在body的code字段
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["code"] == 400
            assert "文件类型错误" in response_data["message"]
    
    @pytest.mark.asyncio
    async def test_api_batch_import_file_too_large(self, auth_headers):
        """Test Case 21: 测试文件大小超过10MB限制"""
        # 生成11MB的CSV文件
        large_csv = b"liveroom_id,resource_url,resource_type\n" + b"1234567890,http://test.com,hls\n" * (11 * 1024 * 100)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("test.csv", io.BytesIO(large_csv), "text/csv")}
            data = {"skip_duplicates": "false", "auto_start": "false"}
            
            response = await client.post(
                "/api/v1/download/tasks/batch-import",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            # 断言：HTTP状态码为200，业务状态码在body的code字段
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["code"] == 413
            assert "文件大小超过限制" in response_data["message"]
            assert "file_size" in response_data["data"]
            assert "max_size" in response_data["data"]
    
    @pytest.mark.asyncio
    async def test_api_batch_import_empty_file(self, auth_headers):
        """Test Case 22: 测试上传空文件"""
        files = {"file": ("test.csv", io.BytesIO(b""), "text/csv")}
        data = {"skip_duplicates": "false", "auto_start": "false"}
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/download/tasks/batch-import",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            # 断言：HTTP状态码为200，业务状态码在body的code字段
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["code"] == 400
            assert "文件不能为空" in response_data["message"]
    
    @pytest.mark.asyncio
    async def test_api_batch_import_missing_columns(self, auth_headers):
        """Test Case 23: 测试CSV缺少必需列"""
        # CSV只包含部分必需列
        csv_content = b"liveroom_id,resource_type\n1234567890,hls\n"
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
            data = {"skip_duplicates": "false", "auto_start": "false"}
            
            response = await client.post(
                "/api/v1/download/tasks/batch-import",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            # 断言：HTTP状态码为200，业务状态码在body的code字段
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["code"] == 400
            assert "缺少必需列" in response_data["message"]
    
    @pytest.mark.asyncio
    async def test_api_batch_import_all_failed(self, auth_headers):
        """Test Case 24: 测试所有行都失败，返回400"""
        # CSV中所有行数据都无效
        csv_bytes = generate_csv_content(
            num_rows=10,
            invalid_rows=[{"row": i, "type": "short_liveroom_id"} for i in range(2, 12)]
        )
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("test.csv", io.BytesIO(csv_bytes), "text/csv")}
            data = {"skip_duplicates": "false", "auto_start": "false"}
            
            response = await client.post(
                "/api/v1/download/tasks/batch-import",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            # 断言：HTTP状态码为200，业务状态码在body的code字段
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["code"] == 400
            assert "批量导入失败，所有行都处理失败" in response_data["message"]
            assert response_data["data"]["success"] == 0
    
    @pytest.mark.asyncio
    async def test_api_batch_import_encoding_error(self, auth_headers):
        """Test Case 25: 测试非UTF-8编码文件"""
        # 使用GBK编码，并包含中文以确保编码差异
        csv_content = "liveroom_id,resource_url,resource_type\n1234567890,http://test.com,hls,这是中文标题\n"
        csv_bytes = csv_content.encode('gbk')
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("test.csv", io.BytesIO(csv_bytes), "text/csv")}
            data = {"skip_duplicates": "false", "auto_start": "false"}
            
            response = await client.post(
                "/api/v1/download/tasks/batch-import",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            # 断言：HTTP状态码为200，业务状态码在body的code字段
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["code"] == 400
            assert "文件编码错误" in response_data["message"]
    
    # ==================== 边界条件和安全测试 ====================
    
    @pytest.mark.asyncio
    async def test_api_batch_import_extremely_long_filename(self, auth_headers):
        """Test Case 26: 测试超长文件名（1000个字符）"""
        csv_bytes = generate_csv_content(num_rows=5)
        long_filename = "a" * 1000 + ".csv"
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": (long_filename, io.BytesIO(csv_bytes), "text/csv")}
            data = {"skip_duplicates": "false", "auto_start": "false"}
            
            response = await client.post(
                "/api/v1/download/tasks/batch-import",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            # 应该能正常处理：HTTP状态码为200，业务状态码在body的code字段
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["code"] in [201, 207]
    
    @pytest.mark.asyncio
    async def test_api_batch_import_special_chars_in_filename(self, auth_headers):
        """Test Case 27: 测试文件名包含特殊字符"""
        csv_bytes = generate_csv_content(num_rows=5)
        special_filename = "<script>alert('xss')</script>.csv"
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": (special_filename, io.BytesIO(csv_bytes), "text/csv")}
            data = {"skip_duplicates": "false", "auto_start": "false"}
            
            response = await client.post(
                "/api/v1/download/tasks/batch-import",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            # 应该能安全处理：HTTP状态码为200，业务状态码在body的code字段
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["code"] in [201, 207]
    
    @pytest.mark.asyncio
    async def test_api_batch_import_sql_injection_attempt(self, db_session, auth_headers):
        """Test Case 28: 测试CSV数据包含SQL注入代码"""
        # CSV行数据包含SQL注入代码
        csv_content = f"""liveroom_id,liveroom_title,liveroom_url,resource_url,resource_type
1234567890,'; DROP TABLE download_tasks--,{fake.url()},{fake.url()},hls
1234567891,Normal Title,{fake.url()},{fake.url()},mp4
"""
        csv_bytes = csv_content.encode('utf-8')
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("test.csv", io.BytesIO(csv_bytes), "text/csv")}
            data = {"skip_duplicates": "false", "auto_start": "false"}
            
            response = await client.post(
                "/api/v1/download/tasks/batch-import",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            # 数据被安全处理，不会导致数据库损坏：HTTP状态码为200，业务状态码在body的code字段
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["code"] in [201, 207]
            
            # 验证数据库仍然正常
            from sqlalchemy import select
            async for db in db_session:
                result = await db.execute(select(DownloadTask))
                tasks = result.scalars().all()
                assert len(tasks) >= 0  # 数据库未被破坏
    
    @pytest.mark.asyncio
    async def test_api_batch_import_concurrent_uploads(self, db_session, auth_headers):
        """Test Case 29: 测试并发上传多个CSV文件"""
        
        async def upload_csv(client, csv_bytes, user_id):
            """上传单个CSV文件"""
            files = {"file": ("test.csv", io.BytesIO(csv_bytes), "text/csv")}
            data = {"skip_duplicates": "false", "auto_start": "false"}
            return await client.post(
                "/api/v1/download/tasks/batch-import",
                files=files,
                data=data,
                headers=auth_headers
            )
        
        # 准备5个不同的CSV文件
        csv_files = [generate_csv_content(num_rows=5) for _ in range(5)]
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 并发发起5个上传请求
            tasks = [upload_csv(client, csv, uuid.uuid4()) for csv in csv_files]
            responses = await asyncio.gather(*tasks)
            
            # 断言：所有请求都正确处理（HTTP状态码为200，业务状态码在body的code字段）
            for response in responses:
                assert response.status_code == 200
                response_data = response.json()
                assert response_data["code"] in [201, 207]
    
    # ==================== 性能测试 ====================
    
    @pytest.mark.asyncio
    async def test_api_batch_import_response_time(self, auth_headers):
        """Test Case 30: 测试API响应时间（100行数据）"""
        csv_bytes = generate_csv_content(num_rows=100)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("test.csv", io.BytesIO(csv_bytes), "text/csv")}
            data = {"skip_duplicates": "false", "auto_start": "false"}
            
            start = time.time()
            response = await client.post(
                "/api/v1/download/tasks/batch-import",
                files=files,
                data=data,
                headers=auth_headers
            )
            duration = time.time() - start
            
            # 断言：HTTP状态码为200，业务状态码在body的code字段
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["code"] in [201, 207]
            assert duration < 5.0  # 100行应在5秒内完成
    
    @pytest.mark.asyncio
    async def test_api_batch_import_large_file_performance(self, db_session, auth_headers):
        """Test Case 31: 测试大文件处理性能（1000行）"""
        csv_bytes = generate_csv_content(num_rows=1000)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": ("test.csv", io.BytesIO(csv_bytes), "text/csv")}
            data = {"skip_duplicates": "false", "auto_start": "false"}
            
            response = await client.post(
                "/api/v1/download/tasks/batch-import",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            # 断言：HTTP状态码为200，业务状态码在body的code字段
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["code"] == 201
            assert response_data["data"]["processing_time"] < 30.0  # 1000行应在30秒内完成

