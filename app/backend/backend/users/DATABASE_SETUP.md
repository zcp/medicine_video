# 数据库设置指南

## 📋 概览

本指南将帮助您设置和初始化用户功能服务的数据库。

## 🛠️ 准备工作

### 1. 环境变量配置

在运行数据库初始化脚本之前，请确保设置了以下环境变量（或使用默认值）：

```bash
export POSTGRES_USER="postgres"           # 默认: postgres
export POSTGRES_PASSWORD="your_password"  # 默认: CHANGE_ME
export POSTGRES_SERVER="localhost"        # 默认: localhost
export POSTGRES_PORT="5432"              # 默认: 5432
export POSTGRES_DB="users_service_db"     # 默认: users_service_db
```

### 2. 数据库依赖

确保已安装所需的 Python 包：

```bash
pip install sqlalchemy psycopg2-binary asyncpg
```

### 3. PostgreSQL 服务

确保 PostgreSQL 服务正在运行，并且目标数据库已创建：

```sql
CREATE DATABASE users_service_db;
```

## 🚀 运行数据库初始化

### 方法1: 模块运行（推荐）

从项目根目录 (`users/`) 运行：

```bash
python -m app.scripts.create_tables
```

### 方法2: 直接运行

```bash
cd users/
python app/scripts/create_tables.py
```

## 📊 创建的数据库表

脚本将创建以下表：

1. **users** - 用户核心表
   - 包含用户基本信息、角色、状态等
   - 支持密码登录和社交登录

2. **membership_products** - 会员产品表
   - 定义可售卖的会员产品
   - 包含产品名称、价格、时长等信息

3. **user_memberships** - 用户会员订阅表
   - 记录用户的会员购买和状态历史
   - 包含订阅状态、到期时间等

## 🔧 高级选项

### 重新创建所有表

如果需要删除现有表并重新创建（**警告：这将删除所有数据**）：

```bash
python -m app.scripts.create_tables --drop
```

### 检查表结构

脚本运行成功后，您可以连接到数据库查看创建的表：

```sql
-- 查看所有表
\dt

-- 查看表结构
\d users
\d membership_products
\d user_memberships
```

## 📝 日志输出

脚本运行时会输出详细的日志信息：

```
2024-01-XX XX:XX:XX - __main__ - INFO - 开始初始化数据库...
2024-01-XX XX:XX:XX - __main__ - INFO - 成功导入数据库引擎和基类
2024-01-XX XX:XX:XX - __main__ - INFO - 成功导入所有模型类
2024-01-XX XX:XX:XX - __main__ - INFO - 将要创建以下数据库表: users, membership_products, user_memberships
2024-01-XX XX:XX:XX - __main__ - INFO - 开始创建数据库表...
2024-01-XX XX:XX:XX - __main__ - INFO - ✅ 数据库表创建成功！
2024-01-XX XX:XX:XX - __main__ - INFO - 数据库中现有表: users, membership_products, user_memberships
2024-01-XX XX:XX:XX - __main__ - INFO - 🎉 操作完成！
```

## ❌ 常见错误

### 1. 连接错误

```
数据库连接失败: could not connect to server
```

**解决方案**：
- 检查 PostgreSQL 服务是否运行
- 验证数据库连接参数
- 确认网络连接

### 2. 权限错误

```
permission denied for database
```

**解决方案**：
- 检查数据库用户权限
- 确保用户有创建表的权限

### 3. 导入错误

```
导入模块失败: No module named 'app'
```

**解决方案**：
- 确保在正确的目录 (`users/`) 下运行脚本
- 检查 Python 路径设置

## 🔍 验证安装

运行以下 SQL 查询验证表是否正确创建：

```sql
-- 检查表是否存在
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('users', 'membership_products', 'user_memberships');

-- 检查约束
SELECT constraint_name, constraint_type 
FROM information_schema.table_constraints 
WHERE table_name IN ('users', 'membership_products', 'user_memberships');

-- 检查索引
SELECT indexname, tablename 
FROM pg_indexes 
WHERE tablename IN ('users', 'membership_products', 'user_memberships');
```

## 📞 技术支持

如果遇到问题，请检查：

1. 数据库连接配置
2. Python 环境和依赖
3. PostgreSQL 服务状态
4. 用户权限设置

更多详细信息，请参考项目文档或联系开发团队。 