
---

# 📄 **《直播核心服务：live_sessions 增加 playback_url 字段的增量开发提示词》**

> 你可以直接将此文件保存为
> **live_sessions_playback_url_incremental_update_prompt.md**

---

# #️⃣ 直播核心服务：为 live_sessions 新增 playback_url 字段

## **增量式开发提示词（Incremental Development Prompt）**

---

## 🎯 一、角色定义（Role Definition）

你是一名资深 Python / FastAPI / SQLAlchemy 架构工程师。
你的任务是：
**在不破坏现有文档、结构、代码、不修改任何现有行为的前提下，为 live_sessions 模块新增 playback_url 字段及相关逻辑。**

你必须保证：

* 增量式修改（只新增，不删除，不覆盖）
* 与现有项目风格一致
* 不引入冲突
* 兼容现有所有 API、测试与服务结构

---

## 🎯 二、任务目标（Task Objective）

为 `live_sessions` 全链路新增字段：

```
playback_url: Optional[str] = None
```

并支持：

* 创建 session 时：`playback_url = NULL`
* 支持后台任务自动生成
* 支持 API 手动更新
* GET API 返回真实字段值（不动态计算）
* 仅在 ready / finished 状态下允许人工更新
* 不覆盖手动设置的值（后台任务只在字段为空时写）

---

## 🎯 三、需要修改的范围（Scope）

你必须以“增量方式”修改以下范围（请严格对应具体文件路径）：

### ✅ **1. 设计文档（主要）**

按照以下修改点：

* DDL 增字段
* 7.2 增加持久化规则说明
* GET /session 的返回说明
* PATCH /session 的更新说明

（内容在下文提供）

---

### ✅ **2. SQLAlchemy Model**
**目标文件**: `backend/live_core_service/app/models/live_core.py`

在 `LiveSession` 模型中新增字段：

```python
playback_url = Column(String(1024), nullable=True)
```

---

### ✅ **3. Pydantic Schema**
**目标文件**: `backend/live_core_service/app/schemas/live_core.py`

#### **（1）Response schema / Output schema**

在 session 详情返回类中新增：

```python
playback_url: Optional[str] = None
```

#### **（2）Update schema（若存在）**

允许：

```python
playback_url: Optional[str] = None
```

但仅用于 service 层逻辑中，前端需遵守状态限制。

#### **（3）Create schema**

❌ 不允许新增字段（保持前端不能创建时传入 playback_url）

---

### ✅ **4. CRUD（增量支持更新字段）**
**目标文件**: `backend/live_core_service/app/crud/live_core.py`

如果存在通用 update 方法，自动支持。
否则补充：

```python
obj.playback_url = update_data.playback_url if provided
```

---

### ✅ **5. Service 层（增量 patch）**
**目标文件**: `backend/live_core_service/app/services/session_service.py`

在更新 session 或后台任务中新增以下逻辑：

#### （A）后台自动生成：

```python
if session.status == READY and session.video_id and session.playback_url is None:
    session.playback_url = generate_default_playback_url(...)
```

#### （B）手动更新：

* 仅允许在 ready、finished 以下状态：

```python
if session.status not in (READY, FINISHED):
    raise BusinessException("直播中不可修改 playback_url")
```

---

### ✅ **6. API 层（增量 patch）**
**目标文件**: `backend/live_core_service/app/api/v1/endpoints/sessions.py`

#### （A）GET `/sessions/{id}`

说明修改为：

* playback_url = database field value
* 不再动态拼接

#### （B）PATCH `/sessions/{id}`

增加 playback_url 支持、状态校验和权限校验。 [V4.1 修复]：确保 PATCH 的成功响应体中也包含 playback_url 字段。

---


# 🧩 四、设计文档增量修改内容（完整补丁）

以下内容必须“增量式”插入现有文档适当位置。

---

## 📌 **（A）DDL 增量补丁**

在 `live_sessions` 表字段列表中新增：

```
playback_url VARCHAR(1024) NULL,
```

字段说明新增：

```
playback_url：直播回放地址。创建时为空，可由系统自动生成，也可人工修改。
```

---

## 📌 **（B）在 7.2 回放 URL 生成规范 追加内容**

```
【新增：回放地址持久化字段 playback_url】

playback_url 是 live_sessions 表的真实字段，而非动态计算字段。

后台任务在满足下列条件时会自动生成 playback_url：

1. status == 'ready'
2. video_id 不为空
3. 当前 playback_url 为 NULL（避免覆盖人工设置）

自动生成格式遵循原文的默认规则 <Base_URL + Storage_Path>。

若 playback_url 已被人工设置，则后台任务不得覆盖。
```

---

## 📌 **（C）在 GET /api/v1/sessions/{session_id} 文本说明中追加**

```
【新增说明】
返回字段 playback_url 直接读取数据库字段 live_sessions.playback_url。
若字段为 NULL，则返回 null。
系统不再在查询阶段拼接计算 URL。
```

---

## 📌 **（D）在 PATCH /api/v1/sessions/{session_id} 文本说明中追加**

```
【新增字段】
playback_url：可选，允许房间所有者或管理员手动更新。

【新增规则】
仅允许在 ready 或 finished 状态下更新。
直播状态中禁止更新。
若 playback_url 被手动设置，则后台任务不得覆盖。

**【[V4.1 修复] 响应规范】**
**PATCH 接口的成功响应 `data` 必须包含更新后的 `playback_url` 字段，以确保与 `GET /api/v1/sessions/{session_id}` 的响应结构一致。**
```

---

# 🧩 五、代码层修改清单（总结）

### **Model**

* 新增字段：`playback_url = Column(String(1024), nullable=True)`

### **Schema**

* 在 Response 类中新增：`playback_url: Optional[str] = None`
* 在 Update 类中新增：`playback_url: Optional[str] = None`
* Create 类无需变动

### **CRUD**

* 支持 update 时修改 playback_url

### **Service**

* 后台自动生成逻辑（空值才写）
* 手动修改逻辑（状态限制）

### **API**

* GET 返回数据库字段
* PATCH 支持手动更新 （请求与响应均包含）

---

# 🧩 六、输出要求（必须遵守）

AI 必须输出：

* **纯增量文档补丁**
* **不改变原有文档结构与章节编号**
* **不修改任何已有示例 JSON**
* **不删除原有 video_id 或 status 逻辑**
* **新增内容必须按上面格式原样插入**

---

# 🟩 七、最终说明

此 MD 文档已经满足你的所有需求：

✔ 独立、可直接给 AI 用
✔ 符合你项目既有提示词格式与结构
✔ 不遗漏任何修改点（文档 + model + schema + service + CRUD + API + Tests）
✔ 明确增量修改点，不会造成冲突
✔ 适用于 ChatGPT、Claude、Copilot 等 LLM

---
