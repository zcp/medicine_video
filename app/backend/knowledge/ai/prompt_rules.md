# AI 辅助开发 - Prompt 规则

> 基于 LiveCore 项目实际代码模式的 Prompt 模板库，更新时间：2026-07-13

---

## 一、文档维护 Prompt

### 1.1 更新 project_summary.md

```
请更新 knowledge/project_summary.md。

要求：
1. 保留历史内容
2. 更新今天完成内容
3. 更新当前开发阶段
4. 更新待办事项
5. 更新风险
6. 更新最近修改文件
7. 更新下一步计划

不要删除已有的重要信息。基于实际代码分析，不要依赖文档假设。
```

### 1.2 记录设计决策

```
请更新 knowledge/decisions.md，添加以下决策：

决策标题：[标题]
决策内容：[简要描述]
原因：
- 原因1
- 原因2
实现方式：[代码示例]
设计考量：
- 考量1
影响：
- 影响1
```

---

## 二、新模块开发 Prompt

### 2.1 创建完整模块（端点 + CRUD + Service + Model + Schema + 测试）

```
请为 [模块名] 创建完整的后端模块。

要求创建以下文件：

1. app/models/[module_name].py
   - 遵循 UUID 主键（default=uuid.uuid4）
   - 包含双时间戳（created_at + updated_at, timezone=True）
   - 如需软删除，使用 is_active 字段
   - 跨服务引用不设外键，添加注释说明

2. app/schemas/[module_name].py
   - 使用 Pydantic v2（from pydantic import BaseModel）
   - 包含 Create、Update、Response schema

3. app/crud/[module_name].py
   - 使用 AsyncSession
   - 实现标准 CRUD（get, get_multi, create, update, delete）
   - 软删除表查询时过滤 is_active = True

4. app/services/[module_name]_service.py
   - 业务逻辑在 Service 层
   - 调用 CRUD 层，不直接操作 Session

5. app/api/v1/endpoints/[module_name].py
   - 创建三级路由器（public_router, user_router, admin_router）
   - 使用 HTTPException 处理错误

6. 在 app/api/v1/api.py 中注册路由
   - import 端点模块
   - 使用 include_router 注册
   - 注意：具体路径必须先于参数化路径注册

7. tests/unit/test_crud_[module_name].py
   - 测试 CRUD 层的基本操作
   - 使用 Mock 隔离数据库

8. tests/integration/test_api_[module_name].py
   - 测试 API 端点的完整流程
   - 使用测试数据库
```

### 2.2 添加数据库迁移

```
请为 [变更描述] 创建数据库迁移文件。

要求：
1. 文件名格式：migrations/YYYYMMDD_描述.sql
2. 使用 IF NOT EXISTS 避免重复执行错误
3. 为新列添加 COMMENT
4. 为新列添加必要的索引
5. 对 is_active 列回填默认值（UPDATE ... WHERE ... IS NULL）

参考示例：
```sql
-- Migration: YYYY-MM-DD
-- [变更描述]

-- 1) 添加新字段
ALTER TABLE table_name ADD COLUMN IF NOT EXISTS column_name TYPE;

-- 2) 回填已有数据
UPDATE table_name SET column_name = default_value WHERE column_name IS NULL;

-- 3) 添加索引
CREATE INDEX IF NOT EXISTS idx_name ON table_name(column_name);
```
```

---

## 三、代码审查 Prompt

```
请对以下代码进行项目特定审查：

[代码内容]

审查要点：
1. UUID 主键是否在应用层生成（default=uuid.uuid4）？
2. 是否包含双时间戳（created_at + updated_at, timezone=True）？
3. 是否需要软删除（is_active）？
4. 跨服务引用是否避免了数据库外键？
5. user_id 取值是否有多级回退逻辑？
6. 是否使用了 SQLAlchemy Enum？
7. 文件处理方法是否遵循"生成路径→验证→保存"模式？
8. 时间戳是否带 timezone=True？
9. 路由是否会在 api.py 中注册？
10. 是否使用 pattern 而非 regex 参数？

输出格式：
- 优点
- 严重问题（必须修改）
- 建议修改
- 总体评价
```

---

## 四、新会话快速恢复 Prompt

```
请按以下顺序恢复项目上下文：

1. 读取 CLAUDE.md（项目基础信息）
2. 读取 knowledge/project_summary.md（当前开发状态）
3. 如果需要架构信息，读取 knowledge/architecture.md
4. 如果需要数据库信息，读取 knowledge/database.md
5. 读取 knowledge/ai/known_issues.md（避免重复已知问题）

然后等待我的任务。
```

---

## 五、测试编写 Prompt

### 5.1 单元测试

```
请为 [CRUD/Service 文件] 编写单元测试。

要求：
1. 使用 pytest + pytest-asyncio
2. 数据库操作使用 Mock 隔离
3. 测试正常情况和异常情况
4. 测试 UUID 应用的边界情况（None 值）
5. 测试软删除过滤逻辑

文件位置：tests/unit/test_[module_name].py
```

### 5.2 集成测试

```
请为 [API 端点] 编写集成测试。

要求：
1. 使用测试数据库
2. 设置正确的鉴权（get_current_user fixture）
3. 验证 HTTP 状态码
4. 验证响应体格式（code, message, data, timestamp）
5. 验证幂等操作（重复调用不创建重复数据）
6. 验证 404 和 401 场景

文件位置：tests/integration/test_api_[module_name].py
```

### 5.3 运行测试

```
pytest tests/unit/test_[module_name].py -v
pytest tests/integration/test_api_[module_name].py -v
pytest --cov=app --cov-report=html  # 查看覆盖率
```

---

## 六、问题排查 Prompt

### 6.1 诊断 404 错误

```
请检查以下问题：
1. 端点文件是否存在？
2. 端点文件是否在 api.py 中 import？
3. 端点文件是否在 api.py 中注册路由？
4. 路由路径是否正确（prefix 拼接）？
5. 路由注册顺序是否正确（具体路径在前）？

执行诊断命令：
python -c "from app.api.v1.api import api_router; [print(r.path, r.methods) for r in api_router.routes]"
```

### 6.2 诊断数据库连接

```
请检查以下问题：
1. .env 文件中的数据库配置是否正确？
2. Docker 容器是否在运行？（docker ps）
3. 数据库端口是否可访问？
4. 密码是否正确？
5. PostgreSQL 是否允许远程连接？

执行诊断命令：
docker ps | grep postgres
docker exec <container_name> psql -U postgres -c "SELECT 1"
```

---

## 七、代码检查 Prompt

### 7.1 检查新代码是否符合项目规范

```
请检查以下代码是否符合 LiveCore 项目规范：

[代码内容]

检查项：
□ UUID 主键：default=uuid.uuid4
□ 双时间戳：created_at + updated_at, timezone=True
□ 软删除：is_active（如适用）
□ 跨服务引用：无数据库外键 + 注释说明
□ 类型注解：所有参数和返回值
□ Docstring：所有公共函数
□ 错误处理：使用 HTTPException
□ 路由注册：api.py 中 import + include_router
□ 测试文件：对应的测试文件已创建

列出不符合项并给出修改建议。
```

---

## 八、执行建议

1. **上下文管理**：复杂任务分阶段执行，每一步保持上下文精简
2. **实际代码优先**：始终基于实际代码分析，不要依赖文档假设
3. **优先使用项目特定 Prompt**：上述 Prompt 已针对项目定制，优先使用
4. **问题优先查 known_issues**：遇到问题先查 `known_issues.md`，避免重复分析

---

**最后更新**：2026-07-13