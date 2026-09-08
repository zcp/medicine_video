# JWT 密钥配置分析报告

## 📋 检查结果

### ✅ 配置文件检查

| 服务 | 配置文件 | JWT_SECRET_KEY 值 | 状态 |
|------|----------|-------------------|------|
| **live_core_service** | `backend/live_core_service/.env` | `your_jwt_secret_key_here_min_32_chars_use_openssl_rand_hex_32` | ⚠️ 占位符 |
| **users** | `backend/users/.env` | `your_jwt_secret_key_here_min_32_chars_use_openssl_rand_hex_32` | ⚠️ 占位符 |
| **Docker 环境** | `.env.docker` | `my-key` | ⚠️ 默认值 |

### ✅ 配置读取方式

两个服务都使用相同的方式读取 JWT 密钥：

**live_core_service** (`app/core/config.py`):
```python
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
```

**users** (`app/core/config.py`):
```python
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
```

### ✅ 环境变量加载顺序

**本地开发环境**（使用 `run.py`）:
1. `live_core_service/run.py`: `load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))`
2. `users/run.py`: `load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))`
3. 每个服务从**各自的 `.env` 文件**加载

**Docker 环境**（使用 `compose-app.yml`）:
1. 两个服务都使用 `env_file: .env.docker`
2. 从**同一个 `.env.docker` 文件**加载

---

## 🎯 问题分析

### ✅ 好消息：配置方式一致

1. **两个服务的 `.env` 文件中的 JWT_SECRET_KEY 值相同**
   - `live_core_service/.env`: `your_jwt_secret_key_here_min_32_chars_use_openssl_rand_hex_32`
   - `users/.env`: `your_jwt_secret_key_here_min_32_chars_use_openssl_rand_hex_32`

2. **配置读取代码一致**
   - 都使用 `os.getenv("JWT_SECRET_KEY", "")`
   - 都使用 `os.getenv("JWT_ALGORITHM", "HS256")`

### ⚠️ 潜在问题

1. **占位符值问题**
   - 两个服务的 `.env` 文件都使用了**占位符值**（`your_jwt_secret_key_here_min_32_chars_use_openssl_rand_hex_32`）
   - 这个值虽然相同，但**不是真正的密钥**，只是示例值

2. **运行时环境变量覆盖**
   - 如果系统环境变量中设置了 `JWT_SECRET_KEY`，会覆盖 `.env` 文件的值
   - 需要检查实际运行时使用的值

3. **Docker 环境配置不一致**
   - `.env.docker` 中使用的是 `my-key`（默认值）
   - 与本地开发环境的 `.env` 文件不一致

---

## 🔍 验证步骤

### 步骤 1：检查实际运行时的 JWT 密钥

**live_core_service** (端口 8000):
```bash
# 查看启动日志，应该能看到配置验证信息
# 或者添加临时日志输出 JWT_SECRET_KEY 的前几个字符
```

**users** (端口 8002):
```bash
# 查看启动日志，应该能看到配置验证信息
# 或者添加临时日志输出 JWT_SECRET_KEY 的前几个字符
```

### 步骤 2：检查系统环境变量

```powershell
# PowerShell
$env:JWT_SECRET_KEY

# 如果返回了值，说明系统环境变量覆盖了 .env 文件
```

### 步骤 3：检查实际使用的密钥

**方法 1：添加临时日志**

在 `live_core_service/app/core/auth.py` 的 `verify_token` 方法中添加：
```python
logger.info(f"JWT_SECRET_KEY 前10个字符: {JWT_SECRET_KEY[:10] if JWT_SECRET_KEY else 'None'}")
```

在 `users/app/services/auth_service.py` 的 `create_access_token` 方法中添加：
```python
logger.info(f"JWT_SECRET_KEY 前10个字符: {self.jwt_secret_key[:10] if self.jwt_secret_key else 'None'}")
```

**方法 2：检查启动日志**

两个服务启动时都会输出配置验证信息，检查是否有 JWT 配置警告。

---

## ✅ 解决方案

### 方案 1：确保使用相同的真实密钥（推荐）

1. **生成新的 JWT 密钥**：
   ```bash
   openssl rand -hex 32
   ```

2. **更新两个服务的 `.env` 文件**：
   ```bash
   # live_core_service/.env
   JWT_SECRET_KEY=<生成的密钥>
   
   # users/.env
   JWT_SECRET_KEY=<相同的密钥>
   ```

3. **更新 `.env.docker`**（如果使用 Docker）：
   ```bash
   # .env.docker
   JWT_SECRET_KEY=<相同的密钥>
   ```

4. **重启两个服务**

### 方案 2：检查并统一环境变量

如果使用系统环境变量：

1. **设置系统环境变量**（Windows）：
   ```powershell
   [System.Environment]::SetEnvironmentVariable("JWT_SECRET_KEY", "<生成的密钥>", "User")
   ```

2. **确保两个服务都能读取到相同的值**

3. **重启两个服务**

---

## 📊 结论

### ✅ 配置方式正确

- ✅ 两个服务使用相同的配置读取方式
- ✅ 两个服务的 `.env` 文件中的 JWT_SECRET_KEY 值相同
- ✅ 配置代码一致

### ⚠️ 需要确认的问题

1. **实际运行时使用的密钥值**
   - `.env` 文件中的值是占位符，需要确认实际运行时使用的值
   - 可能被系统环境变量覆盖

2. **密钥的有效性**
   - 如果使用的是占位符值，JWT 签名验证会失败
   - 需要确保使用真正的密钥

### 🎯 建议

1. **立即检查**：查看两个服务的启动日志，确认实际使用的 JWT_SECRET_KEY 值
2. **统一配置**：如果值不同，统一为相同的真实密钥
3. **验证修复**：重启服务后，重新测试登录流程

---

## 📝 下一步操作

1. ✅ 检查两个服务的启动日志，确认实际使用的 JWT_SECRET_KEY
2. ✅ 如果值不同，统一为相同的真实密钥
3. ✅ 重启两个服务
4. ✅ 重新测试登录流程

