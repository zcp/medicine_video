---
name: live-saas-workflow
description: >-
  Entry router for live-streaming-saas backend repo. Classify request, Read
  matching explorer/backend/docs agent, require user-visible action-checklist
  before edits. Docs live under add-docs/; Docker rebuild live_core only.
---

# Live-Saas 工作流（本仓 · 后端）

## 本 Skill 做什么

根据**用户当前请求**选择角色与改动范围。  
习惯与分流以 [AI-工作约定](add-docs/AI-工作约定.md) 为准。  
不下达用户未点名的功能或文档待办。

**相关文档链接**：凡点名仓库内文件，须用可跳转 Markdown 链接（相对仓库根）；禁止裸路径。细则见 [AI-工作约定 §8](add-docs/AI-工作约定.md)。

> 源自 Live-Saas-Wechat 同名 Skill；本仓已改为后端路径与 `backend` 角色。

## 流程

1. 打开并遵守 [AI-工作约定](add-docs/AI-工作约定.md)
2. 按本轮诉求归类：探索 / 后端实现 / 文档 / 仅建议
3. **Read** 匹配 Agent：[explorer](.cursor/agents/explorer.md) | [backend](.cursor/agents/backend.md) | [docs](.cursor/agents/docs.md)；禁止只贴角色名
4. 新建文档或改后端时，再按下文打开对应规范/模板（按需）
5. 非单句问答 → **必须**启用 [action-checklist](.cursor/skills/action-checklist/SKILL.md)：  
   最小友好方案 → 防填洞 → **可见行动清单** → 按步做 → 自测  
6. 改 `live_core_service` 落地后：提醒 [`rebuild-live-core-only`](rebuild-live-core-only.bat)（不碰 Postgres volume）

---

## 改代码：文档依据与契约对齐（强制）

细则：[AI-工作约定 §4.1](add-docs/AI-工作约定.md)。摘要：

- **先读再改**：命中模块的 [`add-docs`](add-docs/) 设计/增量（Endpoint、Schema、字段表）
- **严格对齐**：字段名、集合、必填、类型、数量、格式、method/path/权限、响应形状
- **写出摘录**：对用户可见摘录必要字段；禁止只写「已对齐」
- **缺口提醒**：文档缺失 / 代码差集 / 行业常见未入库 → 标明建议；**未确认不进代码**

---

## 范围

| 用户意图 | 行为 |
|----------|------|
| 明确要改代码或文档 | 在对应角色边界内完成；先可见清单再改 |
| 只要分析或建议 | 不改仓库、不 commit；仍须可见清单（只读） |
| 报 bug / 排查 | 一律走 [action-checklist](.cursor/skills/action-checklist/SKILL.md) |
| 未提及的主题 | 不主动扩展 |
| 前端小程序 | 契约在本仓 `add-docs`；实现仓为 Live-Saas-Wechat，默认不改本仓冒充前端 |

---

## 新建文档：命名与模板

| 文档类型 | 模板 |
|----------|------|
| 后端模块完整设计 | [后端设计文档模板](add-docs/后端设计文档模板.md) |
| 增量设计（V2/V3…） | [增量设计文档模板](add-docs/增量设计文档模板.md) |
| 已有编号系列 | **沿用该系列已有文首体例与命名**（例：`02-标签管理-V2-…增量设计文档.md`） |

存放：[`add-docs/`](add-docs/)。不随意新增顶层目录。

---

## 改文档 / Skill / Rule / Agent：补丁还是重写

**口令**：意思没变 → 局部补丁；意思变了 → 重写该节。

习惯有变：先改 [AI-工作约定](add-docs/AI-工作约定.md)，再对齐 Cursor 短文件。

---

## 禁止

- 扩大到用户未提出的模块、文档或重构  
- 不套已有模板却自创一套文档结构/命名  
- 与 [AI-工作约定](add-docs/AI-工作约定.md) 冲突的流程  
- 定了角色却不 Read [`.cursor/agents/<角色>.md`](.cursor/agents/)  
- 非单句任务不写可见行动清单  
- 无文档依据发明/改写契约字段  
- 日常 `docker compose down -v` / DROP 库清数据  
