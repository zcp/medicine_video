# backend/media_download_service/tests/README_INTEGRATION_TESTS.md

# 集成测试使用指南

## 概述

集成测试会真实调用爬虫和service层代码，不使用mock，需要真实的网络环境和VZAN账号凭据。

## 前置条件

### 1. 安装依赖
pip install pytest pytest-asyncio httpx playwright
playwright install chromium### 2. 配置环境变量

**Linux/Mac:**
export RUN_INTEGRATION_TESTS=1
export VZAN_USERNAME='你的VZAN用户名'
export VZAN_PASSWORD='你的VZAN密码'
export VZAN_TOKEN='你的VZAN Token'**Windows PowerShell:**
$env:RUN_INTEGRATION_TESTS='1'
$env:VZAN_USERNAME='你的VZAN用户名'
$env:VZAN_PASSWORD='你的VZAN密码'
$env:VZAN_TOKEN='你的VZAN Token'**使用 .env 文件:**
# 创建 .env.test 文件
RUN_INTEGRATION_TESTS=1
VZAN_USERNAME=your_username
VZAN_PASSWORD=your_password
VZAN_TOKEN=your_token

# 加载环境变量
source .env.test  # Linux/Mac## 运行测试

### 运行所有集成测试
cd backend/media_download_service
pytest tests/test_api/test_crawl_and_import_api.py::TestCrawlAndImportAPIIntegration -v -s### 只运行不下载的测试（推荐）
pytest tests/test_api/test_crawl_and_import_api.py::TestCrawlAndImportAPIIntegration::test_crawl_and_import_real_integration -v -s### 运行包含自动下载的测试（⚠️ 会产生真实流量）
pytest tests/test_api/test_crawl_and_import_api.py::TestCrawlAndImportAPIIntegration::test_crawl_and_import_with_auto_start_real -v -s### 跳过集成测试（运行所有其他测试）
pytest tests/test_api/test_crawl_and_import_api.py -v -m "not integration"## 注意事项

1. **网络要求**: 集成测试需要访问VZAN网站，确保网络连接正常
2. **时间消耗**: 真实爬取可能需要几分钟时间
3. **数据清理**: 测试会自动清理创建的数据，但如果测试中断可能有残留
4. **流量消耗**: 带自动下载的测试会产生真实的网络流量
5. **凭据安全**: 不要将凭据提交到代码仓库

## 故障排查

### 测试被跳过
- 检查环境变量是否正确设置
- 运行 `echo $RUN_INTEGRATION_TESTS` 确认

### 爬虫失败
- 检查VZAN账号凭据是否正确
- 检查网络连接
- 检查playwright浏览器是否安装

### 数据库错误
- 确保测试数据库正常运行
- 检查数据库连接配置

### 清理失败
- 手动清理: `DELETE FROM download_tasks WHERE created_at > '测试开始时间';`
- 手动删除文件: 检查 `DOWNLOAD_DIR` 目录

## 输出示例
