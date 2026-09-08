
---

# Service Layer与Data Model一致性验证指令

## 一、验证目标 (Validation Goal)

本次任务的核心目标是，验证 `services/download_service.py` 文件中的业务逻辑代码，是否正确、一致地调用和使用了在 `models/download.py` (SQLAlchemy ORM) 和 `schemas/download.py` (Pydantic Schemas) 中定义的模型、类、字段和函数。

重点是**静态代码层面**的调用关系验证，找出所有潜在的 `AttributeError` (字段不存在)、`TypeError` (类型不匹配) 或逻辑冲突。

## 二、输入文件 (Input Files)

### 2.1. `models/download.py` (数据库ORM模型)
-   **角色**: 定义了与数据库表结构完全对应的Python类，是持久化层的数据契约。

```python
# [请在此处粘贴 models/download.py 文件的完整内容]
```

### 2.2. `schemas/download.py` (Pydantic API模型)
-   **角色**: 定义了API接口的数据结构（请求与响应），负责数据校验、转换和文档化，是API层的数据契约。

```python
# [请在此处粘贴 schemas/download.py 文件的完整内容]
```

### 2.3. `services/download_service.py` (待验证的业务逻辑代码)
-   **角色**: 实现了核心业务逻辑，是连接API层和数据持久化层的桥梁。

```python
# [请在此处粘贴 services/download_service.py 文件的完整内容]
```

## 三、核心验证清单 (Core Validation Checklist)

请根据2.1和2.2节提供的模型定义，对2.3节的`download_service.py`进行以下逐项检查。

### 3.1. 服务层方法签名验证
-   **[ ] 输入参数类型**: 检查 `service` 中所有方法的参数类型注解。特别是那些从 `endpoint` 层接收数据的方法，其类型是否正确地使用了 `schemas.py` 中定义的 **Create** 或 **Update** 模型 (例如 `def create_task(self, *, task_in: schemas.DownloadTaskCreate)`)？
-   **[ ] 返回值类型**: 检查 `service` 中所有方法的返回值类型注解。它是否与实际返回的对象类型（通常是 `models.py` 中定义的ORM实例，或一个ORM实例的列表）一致？

### 3.2. SQLAlchemy 模型 (`models.py`) 使用验证
-   **[ ] 实例化检查**:
    -   在创建ORM实例的代码行（例如 `db_obj = models.DownloadTask(...)`）中，检查传递给构造函数的所有关键字参数（`video_id=...`, `status=...`）是否都是 `DownloadTask` 类中真实定义的列（`Column`）。
-   **[ ] 属性读取检查**:
    -   在代码中，凡是读取ORM实例属性的地方（例如 `task.status` 或 `task.video_id`），检查该属性是否存在于 `models.py` 对应的模型类中。
-   **[ ] 属性写入检查**:
    -   在代码中，凡是修改ORM实例属性的地方（例如 `task.status = 'completed'`），检查该属性是否存在，并且赋的值是否与该列的类型和约束（如`Enum`值）在逻辑上兼容。
-   **[ ] 查询检查**:
    -   在数据库查询语句中（例如 `db.query(models.DownloadTask).filter(models.DownloadTask.status == ...)`），检查 `filter` 或 `order_by` 中使用的模型属性（如 `status`）是否真实存在于模型中。

### 3.3. Pydantic 模型 (`schemas.py`) 使用验证
-   **[ ] 数据转换检查**:
    -   当 `service` 方法从一个 Pydantic `schema` 对象创建 SQLAlchemy `model` 对象时，是否正确地使用了 `.model_dump()` (Pydantic V2) 或 `.dict()` (Pydantic V1) 方法来获取数据字典？
    -   例如，是否存在 `db_obj = models.DownloadTask(**task_in.model_dump())` 这样的正确用法。
-   **[ ] 属性访问检查**:
    -   在 `service` 代码中，是否尝试访问了一个Pydantic输入模型中不存在的字段（例如 `task_in.non_existent_field`）？

## 四、输出要求 (Output Requirements)

1.  **总结**: 在报告开头，给出一个明确的总体结论。
    -   **如果完全一致**: "经详细比对，`services/download_service.py` 与其依赖的 `models.py` 和 `schemas.py` 模型之间**未发现调用与使用上的不一致**。"
    -   **如果存在不一致**: "经详细比对，发现以下 **X** 处潜在的调用不一致问题："

2.  **不一致项列表 (仅在存在不一致时提供)**:
    -   以列表形式清晰地列出每一个差异点。
    -   每个差异点应包含以下信息：
        -   **位置**: `services/download_service.py` 中的函数名和大致行号。
        -   **问题描述**: 清晰描述不一致之处（例如：“尝试访问 `DownloadTaskCreate` schema中不存在的字段`user_name`” 或 “在实例化 `DownloadTask` 模型时传入了未定义的关键字参数 `task_name`”）。
        -   **问题代码片段**: 引用有问题的代码行。
        -   **修正建议**: 提出应如何修改代码以解决这个不一致问题。

**示例差异报告：**
> -   **位置**: `services/download_service.py`, `create_task` 函数
> -   **问题描述**: 在实例化 `models.DownloadTask` 时，使用了关键字参数 `title`，而该模型中对应的字段是 `liveroom_title`。
> -   **问题代码片段**: `db_task = models.DownloadTask(title=task_in.liveroom_title, ...)`
> -   **修正建议**: 应将关键字参数 `title` 修改为 `liveroom_title`，以匹配 `DownloadTask` 模型的定义。即 `db_task = models.DownloadTask(liveroom_title=task_in.liveroom_title, ...)`。