# 直播间与公众号关联 - SQLAlchemy 模型与 Pydantic Schema 一致性检查提示词

**版本**: V1.0  
**创建日期**: 2026-02  
**适用于**: 直播间与公众号关联模块  
**基于文档**: docs/03_系统设计/直播核心功能设计文档_v6_直播间与公众号关联CSM维度设计文档.md

---

## 1. 角色定义 (Role Definition)

你是一名资深的 FastAPI 后端架构师，专注于 API 设计和数据模型的最佳实践。你的任务是审查**直播间与公众号关联**模块的 SQLAlchemy 模型（`liveroom_official_accounts.py`）和 Pydantic Schema（`schemas/liveroom_official_accounts.py`）之间的一致性、安全性和功能适配性。

**核心职责**:
- 验证数据模型的完整性和一致性
- 识别潜在的安全风险和数据泄露问题
- 确保 API 设计符合 RESTful 最佳实践
- 检查数据验证规则的完备性

---

## 2. 任务目标 (Task Objective)

1. 验证 Pydantic Schemas 是否是 SQLAlchemy Models 合理且安全的「API 视图」
2. 确保类型、字段命名、Create/Update/Response 与设计文档 §3 一致
3. 找出任何可能导致数据泄露、验证错误或 API 使用不便的设计缺陷

---

## 3. 核心输入 (Core Input)

- **SQLAlchemy 模型**: `backend/live_core_service/app/models/liveroom_official_accounts.py`（OfficialAccount, LiveRoomOfficialAccount）
- **Pydantic Schema**: `backend/live_core_service/app/schemas/liveroom_official_accounts.py`
- **设计文档 Schema 定义**: 设计文档 §3（OfficialAccountBase/Create/Update/Item、PaginatedData、OfficialAccountAdminListResponse、LiveRoomOfficialAccountsSetRequest/SetResponse/ListResponse、RoomBriefItem、OfficialAccountRoomsListResponse）

请将上述两个代码文件内容及设计文档 §3 作为输入，逐项执行下方审查清单。

---

## 4. 审查清单 (Audit Checklist)

### 4.1 字段命名一致性

- [ ] OfficialAccount 模型字段与 OfficialAccountBase/Create/Update/Item 字段一致（name, slug, app_id, description, is_active, id, created_at, updated_at）
- [ ] 设计文档 Schema 清单与生成代码 Schema 清单逐项对比，无「设计有但代码无」或「代码有但设计无」的偏差（设计为唯一真相来源）

### 4.2 数据类型兼容性

- [ ] UUID → uuid.UUID；String(n) → str + Field(max_length=n)；Boolean → bool；TIMESTAMP(timezone=True) → datetime
- [ ] PaginatedData 复用 content_management 的泛型定义，与设计文档一致

### 4.3 Create / Update / Response Schema

- [ ] OfficialAccountCreate 含 name, slug, app_id, description, is_active；不包含 id, created_at, updated_at
- [ ] OfficialAccountUpdate 各字段 Optional，不包含 id, created_at, updated_at
- [ ] OfficialAccountItem 含 id, is_active, created_at, updated_at 及 Base 字段；model_config from_attributes=True
- [ ] LiveRoomOfficialAccountsSetRequest account_ids 唯一性校验；mode replace/append
- [ ] RoomBriefItem 与 live_rooms 简要字段一致（id, title, slug 等）

### 4.4 安全与规范

- [ ] Response 未暴露敏感字段；name 等校验与设计文档一致（strip、禁止特殊字符）

---

## 5. 最终交付 (Final Deliverable)

输出一份**一致性检查报告**（Markdown），包含：

- 总体评估（通过 / 存在问题）
- 符合性评分（建议百分比）
- 逐项审查结果（与上述清单对应）
- 问题清单（若有）：严重 / 一般，及修正建议
- 结论与是否需要修改代码

报告保存为：`docs/提示词/直播核心功能模块/直播间与公众号关联SQLAlchemy模型与Pydantic模型一致性检查报告.md`
