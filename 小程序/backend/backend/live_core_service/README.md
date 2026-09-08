# LiveCore Service

直播核心功能服务 - 数据库初始化和管理

## 项目结构

```
live_core_service/
├── app/
│   ├── __init__.py
│   ├── database.py         # 数据库配置
│   ├── models/
│   │   ├── __init__.py
│   │   └── live_core.py    # SQLAlchemy模型
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── live_core.py    # Pydantic Schema
│   └── scripts/
│       ├── __init__.py
│       └── create_tables.py # 数据库初始化脚本
├── requirements.txt        # 项目依赖
└── README.md              # 项目说明
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库

编辑 `app/database.py` 文件，配置数据库连接：

```python
DATABASE_URL = "postgresql://username:password@localhost:5432/database_name"
```

或者设置环境变量：

```bash
export DATABASE_URL="postgresql://username:password@localhost:5432/database_name"
```

### 3. 初始化数据库

**推荐方式: 使用模块方式运行**
```bash
cd live_core_service
python -m app.scripts.create_tables
```

**替代方式: 直接运行脚本**
```bash
cd live_core_service
python app/scripts/create_tables.py
```

## 数据库初始化脚本

### 功能特性

- ✅ **自动表创建**: 根据SQLAlchemy模型自动创建所有数据库表
- ✅ **环境检查**: 运行前检查必要文件是否存在
- ✅ **详细日志**: 提供详细的执行日志和错误信息
- ✅ **错误处理**: 完善的异常处理和错误提示
- ✅ **安全退出**: 根据执行结果返回适当的退出码

### 使用方法

**推荐方式:**
```bash
# 从live_core_service目录使用模块方式运行
cd live_core_service
python -m app.scripts.create_tables
```

**替代方式:**
```bash
# 从live_core_service目录直接运行脚本
cd live_core_service
python app/scripts/create_tables.py
```

### 输出示例

```
============================================================
LiveCore Service - 数据库初始化脚本
============================================================
检查运行环境...
当前工作目录: /path/to/live_core_service
[OK] 找到文件: app/database.py
[OK] 找到文件: app/models/live_core.py
[OK] 找到文件: app/__init__.py
[OK] 找到文件: app/models/__init__.py
开始数据库初始化...
成功导入数据库引擎和模型
发现 3 个表需要创建
  - live_rooms
  - live_sessions
  - session_statistics
开始创建数据库表...
[SUCCESS] 数据库表创建成功！
已创建的表:
  [OK] live_rooms
  [OK] live_sessions
  [OK] session_statistics
============================================================
[SUCCESS] 数据库初始化完成！
============================================================
```

### 故障排除

#### 常见错误及解决方案

1. **导入错误**
   ```
   [ERROR] 导入错误: No module named 'app'
   ```
   **解决方案**: 确保从项目根目录 (`live_core_service/`) 运行脚本

2. **数据库连接错误**
   ```
   [ERROR] 数据库初始化失败: connection failed
   ```
   **解决方案**: 
   - 检查数据库服务器是否运行
   - 验证数据库连接配置
   - 确认数据库用户权限

3. **权限错误**
   ```
   [ERROR] 数据库初始化失败: permission denied
   ```
   **解决方案**: 确保数据库用户有创建表的权限

4. **编码错误**
   ```
   UnicodeEncodeError: 'gbk' codec can't encode character
   ```
   **解决方案**: 脚本已修复编码问题，使用UTF-8编码和兼容的字符

## 数据库模型

### 核心表结构

1. **live_rooms** - 直播房间表
   - 存储直播房间的基本信息
   - 支持房间层级结构
   - 包含推流密钥等配置

2. **live_sessions** - 直播会话表
   - 记录每次直播会话的信息
   - 支持多种会话状态
   - 关联录制视频

3. **session_statistics** - 会话统计表
   - 存储直播会话的统计数据
   - 包含观众数、点赞数等指标

## 开发指南

### 添加新模型

1. 在 `app/models/live_core.py` 中定义新模型
2. 在 `scripts/create_tables.py` 中导入新模型
3. 运行初始化脚本创建新表

### 修改现有模型

1. 修改模型定义
2. 使用数据库迁移工具（如Alembic）进行架构变更
3. 或删除表后重新运行初始化脚本（仅开发环境）

## 注意事项

- ⚠️ 此脚本会创建所有表，如果表已存在可能会报错
- ⚠️ 生产环境建议使用数据库迁移工具
- ⚠️ 确保数据库用户有足够的权限
- ⚠️ 建议在运行前备份现有数据 