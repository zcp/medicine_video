# LiveCore 项目 - AI 开发指南

> 本文档包含 LiveCore 项目的基本信息、技术栈、开发规范和常用命令，供 AI 辅助开发时参考。

---

## 项目简介

LiveCore 是一个直播平台的核心后端服务，提供直播房间管理、直播会话管理、专家系统、搜索功能等核心功能。项目采用 FastAPI 框架，使用 PostgreSQL 作为主数据库，Redis 作为缓存和消息队列。

**主要功能模块**：
- 直播房间和会话管理
- 专家系统（专家信息、用户关注、场次专家关联）
- 首页搜索和关键词统计
- 用户行为追踪
- 品牌管理
- 直播场次导入和批量处理
- 文件上传和媒体管理

---

## 技术栈

### 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.100.0 | Web 框架 |
| SQLAlchemy | 1.4.23 | ORM |
| Pydantic | 2.3.0 | 数据验证 |
| PostgreSQL | 15 | 主数据库 |
| asyncpg | 0.30.0 | PostgreSQL 异步驱动 |
| psycopg2-binary | 2.9.1 | PostgreSQL 同步驱动 |
| Redis | 7 | 缓存和消息队列 |
| Celery | 5.3 | 异步任务队列 |
| Uvicorn | 0.15.0 | ASGI 服务器 |
| Python | 3.9+ | 编程语言 |

### 部署技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Docker | - | 容器化 |
| Docker Compose | - | 容器编排 |
| Nginx | alpine | 反向代理 |
| SRS | 6 | 流媒体服务器 |

---

## 项目目录结构

```
D:\live-streaming-saas-v2-main\
├── backend\
│   └── live_core_service\         # 主要后端服务目录
│       ├── app\
│       │   ├── api\               # API endpoints
│       │   │   └── v1\endpoints\  # v1 API 端点
│       │   ├── core\              # 核心功能
│       │   │   ├── auth.py        # 认证相关
│       │   │   ├── config.py      # 配置管理
│       │   │   ├── deps.py        # 依赖注入
│       │   │   ├── exceptions.py  # 异常定义
│       │   │   ├── file_handler.py    # 文件处理
│       │   │   ├── logging_utils.py   # 日志工具
│       │   │   └── response.py    # 响应格式
│       │   ├── crud\              # 数据库操作层
│       │   │   ├── brand.py
│       │   │   ├── session.py
│       │   │   └── ...
│       │   ├── models\            # SQLAlchemy ORM 模型
│       │   │   ├── live_core.py   # 直播核心模型
│       │   │   ├── experts.py     # 专家模型
│       │   │   ├── homepage_search.py
│       │   │   └── ...
│       │   ├── schemas\           # Pydantic 数据模型
│       │   │   ├── brand.py
│       │   │   ├── batch_import.py
│       │   │   └── ...
│       │   ├── services\          # 业务逻辑层
│       │   │   ├── batch_import.py
│       │   │   ├── health_service.py
│       │   │   └── ...
│       │   ├── tasks\             # Celery 异步任务
│       │   │   ├── celery_app.py  # Celery 配置
│       │   │   └── session_processing.py
│       │   ├── database.py        # 数据库连接配置
│       │   ├── main.py            # FastAPI 应用入口
│       │   └── scripts\           # 脚本文件
│       ├── tests\                 # 测试文件
│       │   ├── integration\       # 集成测试
│       │   └── unit\              # 单元测试
│       ├── migrations\            # 数据库迁移文件
│       ├── requirements.txt       # Python 依赖
│       ├── Dockerfile             # Docker 构建文件
│       ├── .env.example           # 环境变量示例
│       ├── run.py                 # 启动脚本
│       └── pytest.ini             # pytest 配置
├── docs\                          # 项目文档
│   ├── 直播saas产品核心说明和开发计划文档.md
│   ├── 技术选型分析报告v1.md
│   └── ...
├── knowledge\                     # AI 知识库
│   ├── README.md
│   ├── project_summary.md
│   ├── architecture.md
│   ├── database.md
│   ├── api.md
│   ├── decisions.md
│   └── ai\
│       ├── prompt_rules.md
│       ├── code_review_rules.md
│       └── known_issues.md
├── compose-app.yml                # Docker Compose 配置（应用服务）
├── compose-db.yml                 # Docker Compose 配置（数据库）
├── compose-srs.yml                # Docker Compose 配置（SRS）
├── pyproject.toml                 # Python 项目配置
└── package.json                   # 项目依赖（前端预留）
```

---

## 开发规范

### 代码分层原则

```
Controller (API endpoints)
    ↓
Service (业务逻辑)
    ↓
CRUD (数据库操作)
    ↓
Models (ORM 模型)
    ↓
Database
```

**职责说明**：
- **Controller (API endpoints)**：负责路由、参数验证、调用 Service
- **Service**：负责业务逻辑处理
- **CRUD**：负责数据库操作
- **Models**：定义数据库表结构和关系
- **Schemas**：定义 API 请求/响应的数据结构

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 文件名 | 小写+下划线 | `live_core.py`, `batch_import.py` |
| 类名 | 大驼峰 | `LiveRoom`, `Expert` |
| 函数名 | 小写+下划线 | `get_db()`, `create_session()` |
| 变量名 | 小写+下划线 | `user_id`, `room_id` |
| 常量名 | 大写+下划线 | `API_V1_STR`, `DATABASE_URL` |
| 表名 | 小写+下划线 | `live_rooms`, `experts` |
| 列名 | 小写+下划线 | `created_at`, `is_active` |

### 代码质量要求

- **圈复杂度**：≤ 10
- **测试覆盖率**：> 80%
- **代码重复率**：≤ 5%
- **所有公共函数必须有 Docstring**
- **所有函数参数和返回值必须有类型注解**

### API 设计规范

- 遵循 RESTful 设计原则
- 使用 Pydantic 进行数据验证
- 统一响应格式（见 `app/core/response.py`）
- 所有 API 路径以 `/api/v1` 开头

---

## 常用命令

### 本地开发

```bash
# 进入后端目录
cd backend/live_core_service

# 创建虚拟环境（首次运行）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（复制并编辑 .env 文件）
cp .env.example .env

# 初始化数据库
python -c "from app.scripts.create_tables import create_tables; create_tables()"

# 启动开发服务器
python run.py

# 或使用 uvicorn 直接启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 测试

```bash
# 进入后端目录
cd backend/live_core_service

# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 运行特定测试文件
pytest tests/unit/test_crud_room.py

# 运行特定测试函数
pytest tests/unit/test_crud_room.py::test_get_room

# 查看测试覆盖率
pytest --cov=app --cov-report=html

# 详细输出
pytest -v

# 只显示失败的测试
pytest -x
```

### 数据库迁移

```bash
# 执行 SQL 迁移文件
# 例如：添加 experts.is_active 字段
psql -U postgres -d live_core_test -f migrations/add_experts_is_active.sql
```

### Docker 部署

```bash
# 构建并启动所有服务
docker-compose -f compose-app.yml up -d

# 只启动 live_core_service
docker-compose -f compose-app.yml up -d live_core_service

# 查看日志
docker-compose -f compose-app.yml logs -f live_core_service

# 停止所有服务
docker-compose -f compose-app.yml down

# 停止并删除所有容器、网络、卷
docker-compose -f compose-app.yml down -v

# 重新构建服务
docker-compose -f compose-app.yml build live_core_service
```

### Celery 异步任务

```bash
# 启动 Celery Worker
celery -A app.tasks.celery_app worker --include=app.tasks.session_processing -l info -c 10

# 查看 Celery 任务状态
celery -A app.tasks.celery_app inspect active

# 清空任务队列
celery -A app.tasks.celery_app purge
```

---

## 环境配置

### 必需的环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| POSTGRES_SERVER | 数据库服务器地址 | localhost |
| POSTGRES_PORT | 数据库端口 | 5432 |
| POSTGRES_USER | 数据库用户名 | postgres |
| POSTGRES_PASSWORD | 数据库密码 | **必须设置** |
| POSTGRES_DB | 数据库名称 | live_core_test |
| CELERY_BROKER_URL | Celery Broker URL | redis://redis:6379/0 |
| CELERY_RESULT_BACKEND | Celery 结果存储 | redis://redis:6379/0 |
| JWT_SECRET_KEY | JWT 密钥 | **必须设置**（≥32字符） |
| JWT_ALGORITHM | JWT 算法 | HS256 |
| CORS_ORIGINS | CORS 允许的源 | * |
| ROOM_MEDIA_ROOT_PATH | 媒体文件根目录 | ./media |
| PLAYBACK_BASE_URL | 回放基础URL | http://localhost:8000 |
| ENVIRONMENT | 环境标识 | development |

### 配置文件位置

- **主配置**：`backend/live_core_service/app/core/config.py`
- **环境变量示例**：`backend/live_core_service/.env.example`
- **Docker 环境变量**：`.env.docker`

---

## 数据库设计

### 主要数据表

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| live_rooms | 直播房间 | id, user_id, title, stream_key |
| live_sessions | 直播会话 | id, room_id, status, start_time, end_time |
| session_statistics | 会话统计 | id, session_id, peak_viewer_count |
| experts | 专家信息 | id, name, title, hospital, is_active |
| user_expert_subscriptions | 用户关注专家 | id, user_id, expert_id |
| live_session_experts | 直播场次专家关联 | id, session_id, expert_id, role |
| categories | 分类 | id, name, slug, parent_id |
| search_keyword_stats | 搜索关键词统计 | id, keyword, keyword_norm, count |
| brands | 品牌信息 | id, name, logo_url |
| user_behavior | 用户行为 | id, user_id, action_type |

### 数据库连接

项目同时支持同步和异步数据库连接：

- **同步连接**：`SessionLocal` - 用于数据库初始化
- **异步连接**：`AsyncSessionLocal` - 用于应用运行时

详见：`backend/live_core_service/app/database.py`

---

## 不应修改的模块

以下模块的核心逻辑不应随意修改：

1. **认证模块** (`app/core/auth.py`)：JWT 认证和授权逻辑
2. **数据库连接** (`app/database.py`)：数据库会话管理
3. **配置管理** (`app/core/config.py`)：环境变量加载和验证
4. **Celery 配置** (`app/tasks/celery_app.py`)：异步任务队列配置

如需修改，请先与团队确认。

---

## 知识库导航

项目知识库位于 `knowledge/` 目录，包含以下文档：

| 文档 | 用途 | 何时查看 |
|------|------|----------|
| [project_summary.md](./knowledge/project_summary.md) | 当前开发状态 | 开发前了解项目进度 |
| [architecture.md](./knowledge/architecture.md) | 系统架构设计 | 架构相关开发 |
| [database.md](./knowledge/database.md) | 数据库设计说明 | 数据库相关开发 |
| [api.md](./knowledge/api.md) | API 接口说明 | API 开发和调试 |
| [decisions.md](./knowledge/decisions.md) | 重要设计决策 | 设计决策时参考 |
| [ai/prompt_rules.md](./knowledge/ai/prompt_rules.md) | 常用 Prompt 模板 | 生成代码或文档时使用 |
| [ai/code_review_rules.md](./knowledge/ai/code_review_rules.md) | 代码审查标准 | 代码审查时参考 |
| [ai/known_issues.md](./knowledge/ai/known_issues.md) | 已知问题和注意事项 | 开发前查看避免重复问题 |

---

## 注意事项

1. **UUID 主键**：所有表使用 UUID 作为主键，在应用层通过 `uuid.uuid4()` 生成
2. **异步优先**：应用运行时使用异步数据库连接，提高性能
3. **时区处理**：所有时间字段使用 `TIMESTAMP(timezone=True)`，存储 UTC 时间
4. **软删除**：使用 `is_active` 字段实现软删除，而不是物理删除
5. **幂等性**：批量导入等操作需要考虑幂等性（`external_room_id`, `playback_url_hash`）
6. **安全验证**：生产环境必须设置强密码，不允许使用默认值

---

## 其他资源

- **项目文档**：`docs/` 目录
- **部署指南**：`部署重建指南.md`
- **Windows 开发环境**：`README-Windows开发环境.md`
- **环境变量配置**：`环境变量配置方案分析.md`

---

**最后更新**: 2026-07-13