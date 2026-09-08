---

# API 实现与设计文档一致性验证指令

## 一、验证目标 (Validation Goal)

本次任务的核心目标是，**严格、逐一地比对** `endpoints/download.py` 和 `services/download_service.py` 中的代码实现，与 `@媒体下载服务设计文档v2.md` **第五章**中定义的API接口设计，并报告两者之间是否存在任何不一致之处。

验证必须覆盖API的路径、HTTP方法、请求/响应结构、状态码以及与服务层的调用关系。

## 二、输入文件 (Input Files)

### 2.1. API 设计规范 (源文档)
-   **源文件**: `@媒体下载服务设计文档v2.md`
-   **对标章节**: 第五章、媒体下载服务 API 接口设计文档（最终版）
-   ** @endpoints\download.py  @service\download_service.py 

## 三、核心验证清单 (Core Validation Checklist)

请根据 **2.1节的API设计规范**，对 `endpoints/download.py 和 service/download_service.py` 的每一个API端点进行逐一验证。

---

### **针对 `POST /api/v1/download/tasks` (创建下载任务):**
-   **[ ] 路径与方法**: `@router` 装饰器是否为 `@router.post("/tasks")`？
-   **[ ] 请求体验证**: 函数是否接受一个Pydantic模型作为请求体，且该模型的字段与设计文档**5.2.1节**的“请求参数示例”一致？
-   **[ ] 成功响应**: 成功时，是否返回 `200` 或 `201` 状态码，且响应JSON的`data`字段内容与**5.2.1节**的“响应示例”结构一致？
-   **[ ] Service调用**: 端点函数是否调用了`download_service.py`中一个命名相似（如`create_task`）的方法？

---

### **针对 `GET /api/v1/download/tasks/{task_id}` (查询任务详情):**
-   **[ ] 路径与方法**: 装饰器是否为 `@router.get("/{task_id}")`？
-   **[ ] 路径参数**: 函数是否正确接收 `task_id` 作为路径参数？
-   **[ ] 成功响应**: 成功时，返回的`data`字段内容是否与设计文档**5.2.2节**的“响应示例”结构一致（包含`task_id`, `task_status`, `progress`等）？
-   **[ ] 404错误处理**: 当传入一个不存在的 `task_id` 时，是否返回 `404 Not Found` 状态码？

---

### **针对 `DELETE /api/v1/download/tasks/{task_id}` (删除/取消任务):**
-   **[ ] 路径与方法**: 装饰器是否为 `@router.delete("/{task_id}")`？
-   **[ ] 成功响应**: 成功取消后，返回的`data`字段中的`task_status`是否为`cancelled`，如设计文档**5.2.3节**所示？

---

**(请继续为设计文档中定义的每一个API端点，按此格式补充验证清单...)**

### **针对所有端点的通用验证:**
-   **[ ] 统一响应结构**: 是否所有端点的返回（包括成功和错误）都严格遵循了设计文档**5.1.1节**定义的`{code, message, data, timestamp}`结构？
-   **[ ] 分页实现**: 对于 `GET /api/v1/download/tasks` 和 `GET /api/v1/download/tasks/{task_id}/failures`，其实现是否处理了 `page`, `size`, `sort` 等查询参数，并且响应`data`的结构符合**5.1.3节**的分页格式？

## 四、输出要求 (Output Requirements)

1.  **总结**: 在报告开头，给出一个明确的总体结论。
    -   **如果完全一致**: "经详细比对，`endpoints/download.py`和`services/download_service.py`的实现与API设计文档 **完全一致**。"
    -   **如果存在不一致**: "经详细比出，代码实现与API设计文档存在以下 **X** 处不一致："

2.  **不一致项列表 (仅在存在不一致时提供)**:
    -   以列表形式清晰地列出每一个差异点。
    -   每个差异点应包含以下信息：
        -   **API端点**: 存在问题的具体接口 (例如: `POST /api/v1/download/tasks`)。
        -   **问题描述**: 清晰描述不一致之处 (例如: "成功响应码应为201，但代码中返回了200")。
        -   **预期规范 (源自文档)**: 引用或描述设计文档中的要求。
        -   **实际实现 (源自代码)**: 描述代码中的实际行为。
        -   **修正建议**: 提出应如何修改代码以符合设计规范。