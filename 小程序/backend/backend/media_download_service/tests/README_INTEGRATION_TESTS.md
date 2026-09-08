# 集成测试使用指南

## 概述

集成测试会真实调用爬虫和service层代码，不使用mock，测试完整的业务流程。

## 快速开始

```bash
# 1. 配置VZAN凭据（在 .env 文件中）
VZAN_USERNAME=你的用户名
VZAN_PASSWORD=你的密码
VZAN_TOKEN=你的token

# 2. 直接运行测试
pytest tests/test_integration.py -v -s
```

## 关键设计原则

### ✅ 测试职责分离

- **测试文件职责**: 验证API功能、数据流转、业务逻辑
- **配置文件职责**: 管理环境配置（由 `app.core.config.settings` 负责）

### ❌ 测试文件不应该做的事

测试文件**不应该**直接检查业务配置环境变量（如 `VZAN_USERNAME`, `VZAN_PASSWORD`, `VZAN_TOKEN`），这些配置由 `settings` 对象统一管理：

```python
# ❌ 错误做法 - 测试文件直接检查业务配置
if not os.getenv("VZAN_USERNAME"):
    pytest.skip("缺少VZAN_USERNAME")

# ✅ 正确做法 - 让业务代码处理配置缺失
# 如果配置缺失，service层会抛出 CrawlerConfigError
# 测试只需验证异常是否被正确处理
```

## 前置条件

### 1. 安装依赖
```bash
pip install pytest pytest-asyncio httpx playwright
playwright install chromium
```

### 2. 配置应用环境变量

**方式1: 使用 .env 文件（推荐）**
```bash
# 编辑 backend/media_download_service/.env
VZAN_USERNAME=你的VZAN用户名
VZAN_PASSWORD=你的VZAN密码
VZAN_TOKEN=你的VZAN_Token
CRAWLER_TIMEOUT=30
CRAWLER_TEMP_DIR=/tmp/crawl_data
DOWNLOAD_DIR=/path/to/downloads
# ... 其他配置
```

**方式2: 使用环境变量（Linux/Mac）**
```bash
export VZAN_USERNAME='你的VZAN用户名'
export VZAN_PASSWORD='你的VZAN密码'
export VZAN_TOKEN='你的VZAN Token'
```

**方式3: 使用环境变量（Windows PowerShell）**
```powershell
$env:VZAN_USERNAME='你的VZAN用户名'
$env:VZAN_PASSWORD='你的VZAN密码'
$env:VZAN_TOKEN='你的VZAN Token'
```

## 运行测试

### 运行所有集成测试
```bash
cd backend/media_download_service
pytest tests/test_integration.py -v -s
```

### 只运行不下载的测试（推荐先运行）
```bash
pytest tests/test_integration.py::TestCrawlAndImportAPIIntegration::test_crawl_and_import_real_integration -v -s
```

### 运行包含自动下载的测试（⚠️ 会产生真实流量和文件）
```bash
pytest tests/test_integration.py::TestCrawlAndImportAPIIntegration::test_crawl_and_import_with_auto_start_real -v -s
```

### 跳过集成测试（运行所有其他测试）
```bash
# 运行所有测试，但跳过标记为 integration 的测试
pytest tests/ -v -m "not integration"
```

### 只运行集成测试
```bash
# 只运行标记为 integration 的测试
pytest tests/ -v -m "integration"
```

## 配置验证流程

```
┌─────────────────┐
│  运行集成测试    │
│  pytest tests/  │
│  test_interation│
│  .py -v -s      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ 发送API请求              │
│ POST /crawl-and-import  │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ API调用Service层         │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Service读取settings配置  │
│ - VZAN_USERNAME         │
│ - VZAN_PASSWORD         │
│ - VZAN_TOKEN            │
└────────┬────────────────┘
         │
         ▼
    ┌────────────┐
    │配置缺失？   │
    └───┬────────┘
        │ 是
        ▼
    ┌──────────────────┐
    │抛出Crawler       │
    │ConfigError       │
    └────┬─────────────┘
         │
         ▼
    ┌────────────────┐
    │API返回错误响应  │
    │code: 400/500   │
    └────┬───────────┘
         │
         ▼
    ┌────────────────┐
    │测试捕获错误    │
    │验证错误处理    │
    └────────────────┘
        │ 否
        ▼
┌─────────────────────────┐
│ 执行爬取和导入          │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ 测试验证结果            │
│ - 爬取状态              │
│ - 导入统计              │
│ - 数据库记录            │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ 清理测试数据            │
│ - 删除数据库记录        │
│ - 清理下载文件          │
└─────────────────────────┘
```

## 测试输出示例

### 成功场景
```
==========================================================
开始真实集成测试
==========================================================
测试前任务数量: 0

发送请求参数: {'crawler_type': 'vzan', 'skip_duplicates': True, ...}

开始执行爬取...
响应状态码: 200

响应数据: {'code': 200, 'data': {...}}

导入统计:
  总数: 15
  成功: 15
  失败: 0
  跳过: 0

生成的CSV文件: /tmp/crawl_data/vzan_20240115_143022.csv

数据库验证:
  测试前任务数: 0
  测试后任务数: 15
  实际创建数: 15
  预期创建数: 15

创建的任务ID (前15个): ['uuid1', 'uuid2', ...]

抽查任务详情:
  任务ID: uuid1
  直播间ID: 1234567890
  直播间标题: 测试直播间
  资源URL: https://example.com/video.m3u8...
  资源类型: hls
  状态: pending

==========================================================
✅ 真实集成测试通过
==========================================================

开始清理测试数据...
已删除 15 个测试任务
清理后任务数量: 0
清理完成
```

### 配置缺失场景（业务代码会处理）
```
开始真实集成测试
发送请求参数: {'crawler_type': 'vzan', ...}

响应状态码: 200
响应数据: {'code': 400, 'message': '爬虫配置错误: 缺少VZAN_USERNAME'}

测试结果: ❌ 预期失败（配置缺失）
```

## 注意事项

1. **网络要求**: 需要访问VZAN网站，确保网络连接正常
2. **时间消耗**: 真实爬取可能需要1-5分钟
3. **数据清理**: 测试会自动清理数据，但如果测试中断可能有残留
4. **流量消耗**: 带自动下载的测试会产生真实的网络流量和文件
5. **凭据安全**: 不要将凭据提交到代码仓库，使用 `.env` 文件并加入 `.gitignore`

## 故障排查

### 测试被跳过
```
SKIPPED [1] 需要设置环境变量 RUN_INTEGRATION_TESTS=1 才运行真实集成测试
```

**解决方案**: 
```bash
export RUN_INTEGRATION_TESTS=1
```

### 爬虫配置错误
```
响应数据: {'code': 400, 'message': '爬虫配置错误: ...'}
```

**解决方案**: 检查 `.env` 文件或环境变量中是否设置了：
- `VZAN_USERNAME`
- `VZAN_PASSWORD`
- `VZAN_TOKEN`

### 数据库连接错误
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**解决方案**: 
1. 确保测试数据库正在运行
2. 检查 `DATABASE_URL` 配置
3. 检查数据库权限

### 浏览器驱动错误
```
playwright._impl._api_types.Error: Executable doesn't exist
```

**解决方案**:
```bash
playwright install chromium
```

## 最佳实践

### 1. 先运行单元测试（使用mock）
```bash
pytest tests/test_api/test_crawl_and_import_api.py -v
```

### 2. 再运行集成测试（不下载）
```bash
export RUN_INTEGRATION_TESTS=1
pytest tests/test_integration.py::TestCrawlAndImportAPIIntegration::test_crawl_and_import_real_integration -v -s
```

### 3. 最后运行完整集成测试（包含下载）
```bash
# 谨慎执行，会产生网络流量
pytest tests/test_integration.py::TestCrawlAndImportAPIIntegration::test_crawl_and_import_with_auto_start_real -v -s
```

### 4. CI/CD环境
```yaml
# .github/workflows/test.yml
- name: Run Integration Tests
  env:
    RUN_INTEGRATION_TESTS: 1
    VZAN_USERNAME: ${{ secrets.VZAN_USERNAME }}
    VZAN_PASSWORD: ${{ secrets.VZAN_PASSWORD }}
    VZAN_TOKEN: ${{ secrets.VZAN_TOKEN }}
  run: |
    pytest tests/test_interation.py -v
```

## 总结

**测试文件的核心职责是验证功能，而不是验证配置。**

- ✅ 验证API是否正确调用Service
- ✅ 验证数据是否正确导入数据库
- ✅ 验证错误是否被正确处理
- ❌ 不检查业务配置环境变量
- ❌ 不关心配置从哪里来
- ❌ 不负责配置的校验

这样的设计遵循了"单一职责原则"，使测试更加清晰、易维护。

