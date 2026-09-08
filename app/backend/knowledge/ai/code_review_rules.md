# AI 辅助开发 - 代码审查规则

> 基于 LiveCore 项目实际代码模式和修复历史定制的审查标准，更新时间：2026-07-13

---

## 一、代码质量指标

### 1.1 通用指标

| 指标 | 要求 | 说明 |
|------|------|------|
| 圈复杂度 | ≤ 10 | 每个函数的复杂度不应超过 10 |
| 代码重复率 | ≤ 5% | 重复代码应提取为函数或模块 |
| 测试覆盖率 | > 80% | 核心模块应达到更高覆盖率 |
| 函数长度 | ≤ 50 行 | 过长函数应拆分 |
| 文件长度 | ≤ 500 行 | 过长文件应拆分为模块 |

---

## 二、项目特有审查清单

### 2.1 UUID 主键生成（必须检查）

**规则**：所有表的 `id` 字段必须在 Python 中通过 `uuid.uuid4()` 生成。

**检查方式**：
```python
# ✅ 正确
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

# ❌ 错误：没有 default
id = Column(UUID(as_uuid=True), primary_key=True)

# ❌ 错误：使用数据库默认值（PostgreSQL 没有 UUID 自动生成）
id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
```

---

### 2.2 双时间戳模式（必须检查）

**规则**：所有业务表必须包含 `created_at` + `updated_at`。

**检查方式**：
```python
# ✅ 正确
created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

# ❌ 错误：缺少 updated_at
# ❌ 错误：缺少 timezone=True
# ❌ 错误：updated_at 没有 onupdate
```

---

### 2.3 软删除模式

**规则**：核心实体表（experts、categories、tags、brands 等）必须使用 `is_active` 软删除。

**检查方式**：
- [ ] 是否有 `is_active` 字段？
- [ ] CRUD 查询时是否过滤 `is_active = True`？
- [ ] 是否有 `idx_*_is_active` 索引？

---

### 2.4 跨服务 user_id 引用

**规则**：对可能独立部署的服务，不设数据库外键，仅添加注释说明。

**检查方式**：
```python
# ✅ 正确
user_id = Column(
    UUID(as_uuid=True),
    nullable=False,
    comment='用户公开ID（users.public_id），应用层验证'
)

# ❌ 错误：对跨服务表设置外键
user_id = Column(
    UUID(as_uuid=True),
    ForeignKey("users.public_id"),  # 跨服务外键
    nullable=False
)
```

---

### 2.5 路由注册完整性（历史高频错误）

**规则**：新增 API 端点时必须完成三步。

**检查方式**：
- [ ] 端点文件是否创建在 `app/api/v1/endpoints/`？
- [ ] 是否在 `app/api/v1/api.py` 中 import？
- [ ] 是否在 `app/api/v1/api.py` 中注册路由？
- [ ] 具体路径是否注册在参数化路径之前？

---

### 2.6 幂等导入模式

**规则**：批量导入功能必须保证幂等性。

**检查方式**：
```python
# ✅ 正确：使用部分唯一索引
__table_args__ = (
    Index(
        "uq_xxx",
        "field1", "field2",
        unique=True,
        postgresql_where=text("field2 IS NOT NULL"),
    ),
)

# ❌ 错误：数据库无唯一约束，仅应用层判断
```

---

### 2.7 文件处理模式

**规则**：文件处理遵循"生成路径 → 验证 → 读取 → 保存 → 返回 URL"模式。

**检查方式**：
- [ ] 是否有独立的 `generate_xxx_path()` 方法？
- [ ] 是否有对应的 `save_xxx()` 方法？
- [ ] 是否有对应的 `delete_old_xxx()` 方法？
- [ ] 是否按时戳命名避免冲突？

---

## 三、安全审查清单

### 3.1 数据安全

- [ ] 所有 API 端点是否进行权限验证？
- [ ] 私有房间的内容是否只有授权用户可见？
- [ ] 敏感信息（密码、Token）是否使用环境变量？
- [ ] 日志中是否打印了敏感信息（密码、Token）？

### 3.2 输入验证

- [ ] 所有用户输入是否使用 Pydantic 进行验证？
- [ ] 文件上传是否有类型和大小限制？
- [ ] UUID 参数是否验证格式？
- [ ] Enum 参数是否验证枚举值？

### 3.3 JWT 安全

- [ ] Token 缺失时是否返回 401？
- [ ] Token 过期时是否返回 401（不能降级为匿名）？
- [ ] 可选鉴权是否正确区分"无 Token"和"Token 无效"？

---

## 四、性能审查清单

### 4.1 数据库性能

- [ ] 是否使用了 `selectinload()` 预加载关联数据（避免 N+1）？
- [ ] 大表查询是否有分页？
- [ ] 是否有必要的索引？
- [ ] 是否有慢查询风险？

### 4.2 异步处理

- [ ] 耗时操作是否使用异步？
- [ ] 大文件上传是否使用流式处理？
- [ ] 数据库连接是否正确使用 `get_async_db()`？

### 4.3 缓存策略

- [ ] 热点数据（首页、焦点图）是否考虑 Redis 缓存？
- [ ] 缓存过期时间是否合理？

---

## 五、可维护性审查清单

### 5.1 代码组织

- [ ] 新功能是否遵循五层架构（API → Service → CRUD → Model）？
- [ ] 是否每个模块都有对应的测试文件？
- [ ] 文件名是否使用小写+下划线？

### 5.2 错误处理

- [ ] 是否使用 HTTPException 而非裸 Exception？
- [ ] 错误信息是否包含足够的上下文？
- [ ] 关键操作是否有日志记录？

### 5.3 类型注解

- [ ] 所有函数参数是否有类型注解？
- [ ] 所有函数返回值是否有类型注解？
- [ ] 公共函数是否有 Docstring？

---

## 六、审查流程

### 6.1 自我审查清单

提交代码前，请逐项检查：

```
□ 路由是否已注册？
□ UUID 是否在应用层生成？
□ 是否有双时间戳？
□ 是否需要软删除？
□ 前端对接是否需要跨服务引用？
□ Pydantic schema 是否完整？
□ 是否有类型注解？
□ 是否需要异步操作？
□ 测试文件是否已创建（或更新）？
□ 日志是否合适（不泄露敏感信息）？
```

### 6.2 同行审查格式

```markdown
## 审查意见

### 优点
- 

### 严重问题（必须修改）
- [文件:行号] 问题描述

### 建议修改
- [文件:行号] 问题描述

### 建议（可选）
- [文件:行号] 建议

### 总体评价
[通过/需修改后重新审查]
```

---

## 七、已知高频问题模式

### 7.1 缺少路由注册

```python
# ❌ 问题：新增了端点文件但没有在 api.py 中注册
# 后果：所有端点返回 404

# ✅ 修复：在 api.py 中添加 import + include_router
```

### 7.2 UUID(None) 崩溃

```python
# ❌ 问题
uuid_obj = UUID(data.get("field"))  # data.get("field") 为 None 时崩溃

# ✅ 修复
value = data.get("field")
if not value:
    raise HTTPException(400, "必需字段缺失")
uuid_obj = UUID(value)
```

### 7.3 Deprecation 警告

```python
# ❌ 问题
mode: str = Query("dry_run", regex="^(dry_run|apply)$")

# ✅ 修复
mode: str = Query("dry_run", pattern="^(dry_run|apply)$")
```

### 7.4 无时区的时间戳

```python
# ❌ 问题
created_at = Column(TIMESTAMP, server_default=func.now())

# ✅ 修复
created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
```

---

## 八、审查工具

| 工具 | 用途 | 命令 |
|------|------|------|
| pytest | 单元测试和集成测试 | `pytest -v` |
| pytest-cov | 测试覆盖率 | `pytest --cov=app --cov-report=html` |
| Flake8 | 代码风格检查 | `flake8 app/` |
| MyPy | 类型检查 | `mypy app/` |

---

## 九、更新记录

| 日期 | 更新内容 |
|------|----------|
| 2026-07-13 | 基于 LiveCore 项目实际代码模式完全重写 |

---

**最后更新**：2026-07-13