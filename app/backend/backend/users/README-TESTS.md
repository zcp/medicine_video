# 用户功能服务测试套件

本文档说明如何设置和运行用户功能服务的测试套件。

## 测试结构

```
tests/
├── conftest.py              # 测试配置和fixtures
├── test_crud_users.py       # CRUD单元测试
├── test_api_auth.py         # 认证API集成测试
└── test_api_users.py        # 用户注册API集成测试
```

## 环境设置

### 1. 安装依赖

```bash
# 安装应用依赖
pip install -r requirements.txt

# 安装测试依赖
pip install -r requirements.txt
```

### 2. 数据库设置

确保PostgreSQL正在运行，并创建测试数据库：

```sql
CREATE DATABASE users_service_test;
```

### 3. 环境变量

创建 `.env` 文件或设置环境变量：

```env
# 数据库配置
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=users_service_test

# Redis配置（可选，测试中会被mock）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
```

## 运行测试

### 运行所有测试

```bash
pytest
```

### 运行特定测试文件

```bash
# 运行CRUD测试
pytest tests/test_crud_users_verified.py

# 运行认证API测试
pytest tests/test_api_auth.py

# 运行用户注册API测试
pytest tests/test_api_users.py
```

### 运行特定测试用例

```bash
# 运行特定的测试类
pytest tests/test_crud_users_verified.py::TestCrudUserCreate

# 运行特定的测试方法
pytest tests/test_crud_users_verified.py::TestCrudUserCreate::test_create_user_success
```

### 显示详细输出

```bash
# 显示详细输出
pytest -v

# 显示标准输出
pytest -s

# 显示覆盖率
pytest --cov=app
```

## 测试覆盖范围

### CRUD层测试 (`test_crud_users.py`)

- ✅ 用户创建成功
- ✅ 重复用户名创建失败
- ✅ 根据用户名查询（包括邮箱作为用户名）
- ✅ 根据邮箱查询
- ✅ 查询不存在的用户

### 认证API测试 (`test_api_auth.py`)

- ✅ 获取图形验证码成功
- ✅ 用户登录成功
- ✅ 密码错误登录失败
- ✅ 验证码错误登录失败
- ✅ 注册场景发送验证码成功
- ✅ 已存在邮箱注册验证码发送失败

### 用户注册API测试 (`test_api_users.py`)

- ✅ 用户注册成功
- ✅ 用户名已存在注册失败
- ✅ 邮箱已存在注册失败
- ✅ 缺少必填字段注册失败
- ✅ 验证码错误注册失败
- ✅ 邮箱格式无效注册失败
- ✅ 密码过短注册失败

## 测试特性

### Mock服务

- **Redis**: 使用`unittest.mock.AsyncMock`模拟Redis操作
- **验证码**: 模拟验证码校验成功/失败场景
- **外部服务**: 不依赖真实的邮件/短信服务

### 数据库

- **隔离**: 每个测试用例在独立的事务中运行
- **清理**: 测试结束后自动回滚数据
- **并发**: 支持并发测试运行

### 断言验证

- **API响应**: 验证HTTP状态码、业务码、响应结构
- **数据库状态**: 验证数据正确创建/更新
- **安全性**: 验证密码不以明文存储
- **默认值**: 验证模型默认值正确设置

## 故障排除

### 常见问题

1. **数据库连接失败**
   ```
   解决方案：检查PostgreSQL服务状态和连接参数
   ```

2. **模块导入错误**
   ```
   解决方案：确保在项目根目录运行，检查PYTHONPATH
   ```

3. **Redis连接错误**
   ```
   解决方案：Redis被mock了，如果仍有错误检查mock配置
   ```

4. **测试数据冲突**
   ```
   解决方案：确保测试数据库为空，或使用随机测试数据
   ```

### 调试测试

```bash
# 运行单个测试并显示详细信息
pytest tests/test_crud_users_verified.py::TestCrudUserCreate::test_create_user_success -v -s

# 进入调试模式
pytest --pdb

# 只运行失败的测试
pytest --lf
```

## 测试最佳实践

1. **数据隔离**: 每个测试使用唯一的测试数据
2. **Mock外部依赖**: 不依赖真实的外部服务
3. **完整验证**: 同时验证API响应和数据库状态
4. **错误场景**: 充分测试各种错误条件
5. **性能考虑**: 使用fixtures复用公共设置

## 持续集成

在CI/CD管道中运行测试：

```yaml
# GitHub Actions示例
- name: Run tests
  run: |
    pytest --cov=app --cov-report=xml
  env:
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
    POSTGRES_SERVER: localhost
    POSTGRES_DB: users_service_test
``` 