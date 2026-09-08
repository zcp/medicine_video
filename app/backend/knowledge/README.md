# 项目知识库导航

> LiveCore 直播 SaaS 平台知识库 | 建立于 2026-07-13

---

## 快速开始

### 新会话恢复（推荐）

在每次新 AI 会话中，使用以下 Prompt 一步恢复上下文：

```
请读取以下文件恢复项目上下文：
1. 根目录 CLAUDE.md（项目基础信息）
2. knowledge/project_summary.md（当前开发状态）
3. knowledge/ai/known_issues.md（已知问题避免重复）
然后等待我的任务。
```

### 按场景查阅

| 场景 | 推荐阅读顺序 |
|------|-------------|
| 新开发者上手 | README → CLAUDE.md → project_summary.md → architecture.md |
| API 开发 | project_summary.md → api.md → architecture.md |
| 数据库变更 | project_summary.md → database.md → decisions.md |
| 架构调整 | architecture.md → database.md → decisions.md |
| 代码审查 | code_review_rules.md → known_issues.md |
| Bug 修复 | known_issues.md → project_summary.md |
| 技术决策 | decisions.md → architecture.md |
| AI 辅助开发 | prompt_rules.md → code_review_rules.md |

---

## 文档清单

### 层级一：项目恒定信息（半年不变）

| 文件 | 大小 | 说明 |
|------|------|------|
| `../CLAUDE.md` | 389 行 | 根目录，AI 自动读取 |

**内容**：项目简介、技术栈、目录结构、开发规范、常用命令、数据库概览、知识库导航

### 层级二：当前开发状态（每日更新）

| 文件 | 大小 | 说明 |
|------|------|------|
| `project_summary.md` | 428 行 | 开发进度看板 |

**内容**：已完成功能（16个模块）、测试覆盖（60+文件）、部署状态（8服务）、待办事项、风险评估

### 层级三：专项文档（按需更新）

| 文件 | 大小 | 说明 |
|------|------|------|
| `architecture.md` | 635 行 | 系统架构设计 |
| `database.md` | 759 行 | 数据库设计文档 |
| `api.md` | 498 行 | API 接口说明 |
| `decisions.md` | 443 行 | 13 项设计决策 |

### 层级四：AI 辅助文档

| 文件 | 大小 | 说明 |
|------|------|------|
| `ai/prompt_rules.md` | 274 行 | 7 类定制 Prompt 模板 |
| `ai/code_review_rules.md` | 311 行 | 7 项项目特定审查规则 |
| `ai/known_issues.md` | 300 行 | 5 个历史问题 + 5 个当前问题 |

---

## 项目统计

| 指标 | 数值 |
|------|------|
| API 模块 | 17 个端点文件 |
| 数据库表 | 28 张 |
| 服务模块 | 14 个 CRUD + 17 个 Service |
| ORM 模型 | 11 个模块 |
| 单元测试 | 41 个文件 |
| 集成测试 | 33 个文件 |
| Docker 服务 | 8 个 |
| 设计决策 | 13 项已记录 |
| 知识库总量 | 4,490 行 |

---

## 维护规范

### 更新时机

| 场景 | 需更新文档 |
|------|-----------|
| 新增功能模块 | project_summary.md |
| 数据库表变更 | database.md + 迁移 SQL |
| 技术决策 | decisions.md |
| 架构调整 | architecture.md |
| Bug 修复（有教训） | known_issues.md |
| 新增 API | api.md |
| 项目状态变化 | project_summary.md |

### 更新方式

在 AI 会话中执行：
```
请更新 knowledge/project_summary.md，记录本次 [变更类型]：[变更描述]
```

### 质量原则

1. **基于实际代码**：所有内容必须与实际代码一致，不得基于文档假设
2. **保持精简**：CLAUDE.md ≤ 500 行（当前 389 行，有 111 行余量）
3. **链接完整**：文档间交叉引用指向存在的文件
4. **按时更新**：project_summary 每次重要变更后更新

---

## 目录结构

```
CLAUDE.md                         ⭐ 根目录，AI 自动读取
knowledge/
├── CLAUDE.md                     ⭐ 硬链接，与根目录同步
├── README.md                     📖 本文件
├── project_summary.md            📋 开发进度看板
├── architecture.md               🏗 系统架构
├── database.md                   🗄 数据库设计（28 张表）
├── api.md                        🔌 API 接口
├── decisions.md                  📝 设计决策（13 项）
└── ai/
    ├── prompt_rules.md           🤖 Prompt 模板库
    ├── code_review_rules.md      ✅ 代码审查标准
    └── known_issues.md           ⚠️ 已知问题列表
```

---

**最后更新**：2026-07-13