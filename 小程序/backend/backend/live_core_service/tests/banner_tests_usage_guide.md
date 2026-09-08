# Banner上传功能增量测试代码使用指南

## 📋 概述

本指南说明如何将新生成的banner上传功能测试代码集成到现有的测试套件中。

## 📁 生成的文件

### 1. Service层测试
**文件**: `tests/unit/test_service_topic_banner_increment.py`
- 包含 `TestTopicBannerManagement` 类
- 6个测试函数，覆盖所有Service层业务逻辑

### 2. API端点测试
**文件**: `tests/integration/test_api_topic_banner_increment.py`
- 包含 `TestTopicBannerAPI` 类（5个测试函数）
- 3个辅助函数（create_test_image, create_oversized_image, create_invalid_file）

## 🚀 集成步骤

### 方案一：独立测试文件（推荐）

**✅ 优点**：
- 不修改现有测试文件
- 完全隔离，零风险
- 可以单独运行banner相关测试

**操作步骤**：
```bash
# 1. 文件已经生成，直接运行测试
cd backend/live_core_service

# 2. 运行Service层测试
pytest tests/unit/test_service_topic_banner_increment.py -v

# 3. 运行API端点测试
pytest tests/integration/test_api_topic_banner_increment.py -v

# 4. 运行所有banner相关测试
pytest tests/unit/test_service_topic_banner_increment.py tests/integration/test_api_topic_banner_increment.py -v
```

### 方案二：合并到现有测试文件

**⚠️ 注意**：只有在确认现有测试稳定后才建议使用此方案。

#### Step 1: 合并Service层测试

```bash
# 1. 打开现有测试文件
# tests/unit/test_service_topic.py

# 2. 在文件末尾添加以下内容（从 test_service_topic_banner_increment.py 复制）：
#    - TestTopicBannerManagement 类（包含6个测试函数）

# 3. 确保导入语句包含：
from fastapi import UploadFile, HTTPException
```

#### Step 2: 合并API端点测试

```bash
# 1. 打开现有测试文件
# tests/integration/test_api_topic.py

# 2. 在文件末尾添加以下内容（从 test_api_topic_banner_increment.py 复制）：
#    - TestTopicBannerAPI 类（包含5个测试函数）
#    - 三个辅助函数

# 3. 确保导入语句包含：
from io import BytesIO
from PIL import Image
```

## ✅ 测试覆盖清单

### Service层测试（6个）
- [x] ✅ 成功上传横幅
- [x] ✅ 专题不存在
- [x] ✅ 权限不足
- [x] ✅ 删除旧横幅文件
- [x] ✅ 文件验证失败
- [x] ✅ 数据库更新失败

### API端点测试（5个）
- [x] ✅ 成功上传横幅
- [x] ✅ 专题不存在（404）
- [x] ✅ 权限不足（403）
- [x] ✅ 无效文件类型（400）
- [x] ✅ 文件过大（400）

## 🔧 依赖项

确保已安装以下依赖：

```bash
pip install Pillow  # 用于生成测试图片
```

## 🧪 运行测试

### 运行所有专题相关测试

```bash
# Service层
pytest tests/unit/test_service_topic.py tests/unit/test_service_topic_banner_increment.py -v

# API端点
pytest tests/integration/test_api_topic.py tests/integration/test_api_topic_banner_increment.py -v
```

### 只运行banner相关测试

```bash
# Service层
pytest tests/unit/test_service_topic_banner_increment.py::TestTopicBannerManagement -v

# API端点
pytest tests/integration/test_api_topic_banner_increment.py::TestTopicBannerAPI -v
```

### 运行特定测试

```bash
# 运行成功上传测试
pytest tests/unit/test_service_topic_banner_increment.py::TestTopicBannerManagement::test_upload_topic_banner_success -v

# 运行权限测试
pytest tests/integration/test_api_topic_banner_increment.py::TestTopicBannerAPI::test_upload_banner_permission_denied -v
```

## 📊 测试报告

生成覆盖率报告：

```bash
# 生成HTML覆盖率报告
pytest tests/unit/test_service_topic_banner_increment.py \
       tests/integration/test_api_topic_banner_increment.py \
       --cov=app.services.topic_service \
       --cov=app.api.v1.endpoints.topic \
       --cov=app.core.file_handler \
       --cov-report=html

# 查看报告
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

## ⚠️ 注意事项

### 1. Mock路径
Service层测试使用正确的Mock路径：
```python
# ✅ 正确
mocker.patch("app.crud.topic.get", ...)
mocker.patch("app.core.file_handler.FileHandler.save_banner_file", ...)

# ❌ 错误
mocker.patch("app.crud_topic.get", ...)  # 使用别名路径
```

### 2. API测试Fixture
API测试必须使用 `topic_client` fixture：
```python
# ✅ 正确
async def test_upload_banner_success(self, topic_client):
    async for client, app, db in topic_client:
        ...

# ❌ 错误
async def test_upload_banner_success(self, async_client, db_session):
    ...
```

### 3. 清理依赖覆盖
每个API测试必须清理 `dependency_overrides`：
```python
try:
    # 测试代码
    pass
finally:
    app.dependency_overrides.clear()  # ✅ 必须清理
```

## 🐛 故障排除

### 问题1: 导入错误
```bash
ImportError: cannot import name 'UploadFile' from 'fastapi'
```
**解决**: 确保在测试文件顶部添加导入：
```python
from fastapi import UploadFile, HTTPException
```

### 问题2: Pillow未安装
```bash
ModuleNotFoundError: No module named 'PIL'
```
**解决**: 安装Pillow：
```bash
pip install Pillow
```

### 问题3: 401 Unauthorized
```bash
response.status_code == 401  # 期望200
```
**解决**: 确保使用 `topic_client` fixture并正确设置 `dependency_overrides`

### 问题4: Mock未生效
```bash
AssertionError: Expected mock to be called once
```
**解决**: 检查Mock路径是否正确（使用原始模块路径，不是别名）

## 📚 相关文档

- [Service层测试提示词](docs/提示词/专题功能---Service层测试代码生成提示词---第二阶段.md)
- [API端点测试提示词](docs/提示词/专题功能---API端点测试代码生成提示词.md)
- [Banner上传增量测试提示词](docs/提示词/专题功能banner上传-增量测试代码生成提示词.md)
- [增量开发提示词](docs/提示词/专题功能增加banner上传接口-增量开发提示词.md)

## ✨ 最佳实践

1. **先运行独立测试文件**，确认测试通过后再考虑合并
2. **定期运行所有测试**，确保没有破坏现有功能
3. **使用覆盖率工具**，确保测试覆盖关键代码路径
4. **保持测试独立**，每个测试都应该能单独运行
5. **遵循AAA模式**（Arrange-Act-Assert）组织测试代码

---

**生成日期**: 2025-10-21
**版本**: 1.0.0

