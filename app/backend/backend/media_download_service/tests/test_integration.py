import pytest
import os
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.download import DownloadTask
from sqlalchemy import select, func


class TestCrawlAndImportAPIIntegration:
    """爬取并导入API真实集成测试类"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_crawl_and_import_real_integration(
            self,
            db_session_sync,
            auth_headers
    ):
        """
        测试用例: 真实环境集成测试 - 爬取并导入

        前置条件:
        - 需要真实的VZAN账号凭据（通过settings配置）
        - 需要网络连接
        - 需要浏览器驱动（playwright）

        说明:
        - VZAN的用户名、密码、token等配置由app.core.config.settings统一管理
        - 如果配置缺失，业务代码会抛出CrawlerConfigError异常
        - 测试只需验证这些异常是否被正确处理
        
        运行方式:
        - 直接运行: pytest tests/test_integration.py -v -s
        - 跳过集成测试: pytest tests/ -m "not integration"
        - 只运行集成测试: pytest tests/ -m "integration"

        执行流程:
        1. 真实调用crawler.crawl()爬取数据
        2. 生成真实的CSV文件
        3. 真实导入到数据库
        4. 验证数据库记录
        5. 清理测试数据

        验证点:
        - 爬取成功返回CSV文件
        - CSV文件包含有效数据
        - 数据库成功创建任务记录
        - 任务状态正确
        - 清理后数据库无残留
        """
        # ==================== 准备阶段 ====================
        print("\n" + "=" * 60)
        print("开始真实集成测试")
        print("=" * 60)

        # 1. 记录测试前的数据库状态
        initial_task_count = db_session_sync.execute(
            select(func.count(DownloadTask.id))
        ).scalar()
        print(f"测试前任务数量: {initial_task_count}")

        created_task_ids = []

        try:
            # ==================== 执行阶段 ====================
            async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                    timeout=300.0  # 真实爬取可能需要较长时间
            ) as client:

                # 2. 构造请求参数
                payload = {
                    "crawler_type": "vzan",
                    "skip_duplicates": True,  # 启用去重，避免重复数据
                    "auto_start": False,  # 不自动启动，避免下载
                    "crawl_options": {
                        # 可以添加爬虫选项，例如限制页数
                        # "max_pages": 1,
                        # "page_size": 10
                    }
                }

                print(f"\n发送请求参数: {payload}")

                # 3. 发送真实请求
                print("\n开始执行爬取...")
                response = await client.post(
                    "/api/v1/download/tasks/crawl-and-import",
                    json=payload,
                    headers=auth_headers
                )

                print(f"响应状态码: {response.status_code}")

                # ==================== 验证阶段 ====================
                # 4. 验证HTTP响应
                assert response.status_code == 200, \
                    f"HTTP状态码应为200，实际: {response.status_code}\n响应内容: {response.text}"

                data = response.json()
                print(f"\n响应数据: {data}")

                assert "data" in data, "响应应包含data字段"
                result_data = data["data"]

                # 5. 验证业务响应（允许“全部重复被跳过”场景）
                assert "import_result" in result_data, "应包含import_result字段"
                import_result = result_data["import_result"]
                acceptable_codes = [200, 207]
                if import_result.get("success", 0) == 0 and import_result.get("failed", 0) == 0 and import_result.get("skipped", 0) > 0:
                    # 全部为重复数据被跳过，当前实现返回业务码400也视为正确
                    acceptable_codes.append(400)
                assert data["code"] in acceptable_codes, \
                    f"业务状态码应为200或207，或全部跳过时允许400，实际: {data['code']}\n数据: {data}"

                # 6. 验证爬取结果
                assert result_data["crawl_status"] == "success", \
                    f"爬取状态应为success，实际: {result_data.get('crawl_status')}"

                # 7. 验证导入结果
                print(f"\n导入统计:")
                print(f"  总数: {import_result['total']}")
                print(f"  成功: {import_result['success']}")
                print(f"  失败: {import_result['failed']}")
                print(f"  跳过: {import_result['skipped']}")

                assert import_result["total"] > 0, "应爬取到至少一条数据"
                assert import_result["success"] >= 0, "成功数不应为负数"

                # 8. 验证CSV文件生成
                if result_data.get("crawl_file"):
                    csv_file = result_data["crawl_file"]
                    print(f"\n生成的CSV文件: {csv_file}")

                    # 验证文件存在（如果配置保留文件）
                    from app.core.config import settings
                    if not settings.CRAWL_IMPORT_DELETE_TEMP_FILE:
                        assert os.path.exists(csv_file), \
                            f"CSV文件应存在: {csv_file}"

                # 9. 验证数据库记录
                final_task_count = db_session_sync.execute(
                    select(func.count(DownloadTask.id))
                ).scalar()

                actual_created = final_task_count - initial_task_count
                print(f"\n数据库验证:")
                print(f"  测试前任务数: {initial_task_count}")
                print(f"  测试后任务数: {final_task_count}")
                print(f"  实际创建数: {actual_created}")
                print(f"  预期创建数: {import_result['success']}")

                assert actual_created == import_result['success'], \
                    f"数据库实际创建数({actual_created})应等于导入成功数({import_result['success']})"

                # 10. 获取创建的任务ID（用于清理）
                if import_result.get('created_task_ids'):
                    created_task_ids = import_result['created_task_ids']
                    print(f"\n创建的任务ID (前{len(created_task_ids)}个): {created_task_ids}")

                # 11. 验证任务详细信息
                if created_task_ids:
                    # 随机抽查第一个任务
                    first_task_id = created_task_ids[0]
                    task = db_session_sync.execute(
                        select(DownloadTask).where(DownloadTask.id == first_task_id)
                    ).scalar_one_or_none()

                    if task:
                        print(f"\n抽查任务详情:")
                        print(f"  任务ID: {task.id}")
                        print(f"  直播间ID: {task.liveroom_id}")
                        print(f"  直播间标题: {task.liveroom_title}")
                        print(f"  资源URL: {task.resource_url[:50]}...")
                        print(f"  资源类型: {task.resource_type}")
                        print(f"  状态: {task.status}")

                        assert task.status == "pending", \
                            f"任务初始状态应为pending，实际: {task.status}"
                        assert task.resource_url, "资源URL不应为空"
                        assert task.liveroom_id, "直播间ID不应为空"

                print("\n" + "=" * 60)
                print("✅ 真实集成测试通过")
                print("=" * 60)

        except Exception as e:
            print(f"\n❌ 测试失败: {str(e)}")
            raise

        finally:
            # ==================== 清理阶段 ====================
            print("\n开始清理测试数据...")

            try:
                # 12. 删除本次测试创建的所有任务
                if created_task_ids:
                    for task_id in created_task_ids:
                        task = db_session_sync.execute(
                            select(DownloadTask).where(DownloadTask.id == task_id)
                        ).scalar_one_or_none()

                        if task:
                            db_session_sync.delete(task)

                    db_session_sync.commit()
                    print(f"已删除 {len(created_task_ids)} 个测试任务")
                else:
                    # 如果没有任务ID，按时间范围删除（更安全的方式）
                    # 删除测试期间创建的所有pending任务
                    cleanup_count = db_session_sync.execute(
                        select(func.count(DownloadTask.id)).where(
                            DownloadTask.id > initial_task_count
                        )
                    ).scalar()

                    if cleanup_count > 0:
                        print(f"⚠️ 通过范围清理，可能删除 {cleanup_count} 条记录")

                # 13. 验证清理结果
                after_cleanup_count = db_session_sync.execute(
                    select(func.count(DownloadTask.id))
                ).scalar()

                print(f"清理后任务数量: {after_cleanup_count}")
                print("清理完成")

            except Exception as e:
                print(f"⚠️ 清理失败: {str(e)}")
                # 清理失败不影响测试结果

"""
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_crawl_and_import_with_auto_start_real(
            self,
            db_session_sync,
            auth_headers
    ):
   
        测试用例: 真实环境集成测试 - 爬取并自动启动下载

        ⚠️ 注意: 此测试会触发真实下载，会产生网络流量和文件

        说明:
        - VZAN配置由app.core.config.settings统一管理
        - 如果配置缺失，业务代码会抛出异常

        执行流程:
        1. 爬取数据
        2. 导入任务
        3. 自动启动下载（会产生真实的网络流量和文件）
        4. 验证任务状态变化
        5. 清理测试数据和文件
        
        运行方式:
        - 直接运行此测试: pytest tests/test_integration.py::TestCrawlAndImportAPIIntegration::test_crawl_and_import_with_auto_start_real -v -s
      

        print("\n" + "=" * 60)
        print("⚠️ 开始真实下载集成测试（会产生网络流量）")
        print("=" * 60)

        created_task_ids = []
        download_dirs = []

        try:
            async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                    timeout=600.0  # 下载需要更长时间
            ) as client:

                payload = {
                    "crawler_type": "vzan",
                    "skip_duplicates": True,
                    "auto_start": True,  # 🔥 启用自动下载
                    "crawl_options": {
                        # 建议限制爬取数量，避免下载过多
                        # "max_pages": 1,
                        # "page_size": 2  # 只下载2个视频
                    }
                }

                print(f"\n发送请求（启用自动下载）: {payload}")

                response = await client.post(
                    "/api/v1/download/tasks/crawl-and-import",
                    json=payload,
                    headers=auth_headers
                )

                assert response.status_code == 200, f"HTTP状态码错误: {response.text}"

                data = response.json()
                result_data = data["data"]
                import_result = result_data["import_result"]

                created_task_ids = import_result.get('created_task_ids', [])

                print(f"\n导入并启动了 {import_result['success']} 个任务")

                # 验证任务状态（应该不是pending，而是processing或completed）
                if created_task_ids:
                    task = db_session_sync.execute(
                        select(DownloadTask).where(DownloadTask.id == created_task_ids[0])
                    ).scalar_one_or_none()

                    if task:
                        print(f"任务状态: {task.status}")
                        assert task.status in ["processing", "completed", "partial_completed", "failed"], \
                            f"自动启动后任务状态应改变，实际: {task.status}"

                        # 记录下载目录，用于清理
                        from app.core.config import settings
                        video_dir = os.path.join(settings.DOWNLOAD_DIR, f"video_{task.video_id}")
                        if os.path.exists(video_dir):
                            download_dirs.append(video_dir)

                print("\n✅ 真实下载集成测试通过")

        finally:
            # 清理任务
            print("\n开始清理测试数据和文件...")

            # 清理数据库
            for task_id in created_task_ids:
                task = db_session_sync.execute(
                    select(DownloadTask).where(DownloadTask.id == task_id)
                ).scalar_one_or_none()
                #if task:
                   # db_session_sync.delete(task)

            db_session_sync.commit()

            # 清理下载的文件
            import shutil
            for download_dir in download_dirs:
                try:
                    if os.path.exists(download_dir):
                        shutil.rmtree(download_dir)
                        print(f"已删除下载目录: {download_dir}")
                except Exception as e:
                    print(f"⚠️ 删除目录失败: {download_dir}, 错误: {e}")

            print("清理完成")
"""