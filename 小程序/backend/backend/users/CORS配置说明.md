# CORS 配置说明

## ✅ 已修复的问题

### 问题
前端（`http://localhost:5174`）访问后端（`http://localhost:8002`）时出现 CORS 错误：
```
Access to XMLHttpRequest at 'http://localhost:8002/api/v1/auth/captcha' 
from origin 'http://localhost:5174' has been blocked by CORS policy
```

### 解决方案
已更新 `app/main.py` 中的 CORS 配置，现在支持：

1. ✅ **本地开发环境** - 自动包含所有常用端口
2. ✅ **生产环境** - 从环境变量读取，支持多个域名
3. ✅ **完整的 CORS 设置** - 包括 `expose_headers`

## 📋 配置详情

### 本地开发环境（自动配置）

以下源会自动允许：

```python
local_origins = [
    "http://localhost:5174",      # user_service_frontend 项目
    "http://127.0.0.1:5174",       # user_service_frontend 项目（127.0.0.1）
    "http://localhost:5173",       # 其他前端项目
    "http://127.0.0.1:5173",       # 其他前端项目（127.0.0.1）
    "http://localhost:9500",       # 其他端口
    "http://127.0.0.1:9500",       # 其他端口（127.0.0.1）
]
```

### 生产环境（环境变量配置）

通过环境变量 `CORS_ALLOWED_ORIGINS` 配置生产域名：

```bash
# 单个域名
CORS_ALLOWED_ORIGINS=https://mp.dayilive.com

# 多个域名（用逗号分隔）
CORS_ALLOWED_ORIGINS=https://mp.dayilive.com,https://www.mp.dayilive.com
```

**默认值：** 如果没有设置环境变量，默认使用：
```
https://mp.dayilive.com,https://www.mp.dayilive.com
```

## 🚀 使用方法

### 本地开发

**无需任何配置！** 直接运行：

```bash
cd live-streaming-saas/backend/users
uvicorn app.main:app --reload --port 8002
```

前端会自动被允许访问。

### 生产环境部署

#### 方法 1：环境变量（推荐）

在部署时设置环境变量：

```bash
# Linux/Mac
export CORS_ALLOWED_ORIGINS="https://mp.dayilive.com,https://www.mp.dayilive.com"

# Windows PowerShell
$env:CORS_ALLOWED_ORIGINS="https://mp.dayilive.com,https://www.mp.dayilive.com"

# 然后启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8002
```

#### 方法 2：.env 文件

创建 `.env` 文件：

```bash
CORS_ALLOWED_ORIGINS=https://mp.dayilive.com,https://www.mp.dayilive.com
```

然后使用 `python-dotenv` 加载：

```python
from dotenv import load_dotenv
load_dotenv()
```

#### 方法 3：Docker 环境变量

在 `docker-compose.yml` 或 Docker 运行时设置：

```yaml
environment:
  - CORS_ALLOWED_ORIGINS=https://mp.dayilive.com,https://www.mp.dayilive.com
```

或：

```bash
docker run -e CORS_ALLOWED_ORIGINS="https://mp.dayilive.com,https://www.mp.dayilive.com" ...
```

## 🔍 验证 CORS 配置

### 1. 检查配置是否正确

启动后端服务后，访问：

```
http://localhost:8002/docs
```

查看 API 文档，测试 CORS 是否正常工作。

### 2. 测试前端请求

在前端浏览器控制台运行：

```javascript
fetch('http://localhost:8002/api/v1/auth/captcha', {
  method: 'GET',
  credentials: 'include'
})
  .then(res => res.json())
  .then(data => console.log('✅ CORS 正常', data))
  .catch(err => console.error('❌ CORS 错误', err))
```

### 3. 检查响应头

在浏览器开发者工具的 Network 标签中，查看响应头：

```
Access-Control-Allow-Origin: http://localhost:5174
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: *
Access-Control-Allow-Headers: *
```

## ⚙️ CORS 配置参数说明

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # 允许的来源列表
    allow_credentials=True,         # 允许携带凭证（cookies）
    allow_methods=["*"],            # 允许所有 HTTP 方法
    allow_headers=["*"],            # 允许所有请求头
    expose_headers=["*"],           # 暴露所有响应头给前端
)
```

### 参数说明

- **`allow_origins`**: 允许的来源（域名+端口）
- **`allow_credentials`**: 允许携带 cookies 和认证信息
- **`allow_methods`**: 允许的 HTTP 方法（GET, POST, PUT, DELETE 等）
- **`allow_headers`**: 允许的请求头（Authorization, Content-Type 等）
- **`expose_headers`**: 暴露给前端的响应头

## 🔧 常见问题

### Q1: 为什么需要同时支持 localhost 和 127.0.0.1？

**A:** 不同浏览器和系统可能使用不同的地址格式。为了兼容性，两种格式都支持。

### Q2: 生产环境如何添加新域名？

**A:** 修改环境变量 `CORS_ALLOWED_ORIGINS`，用逗号分隔多个域名：

```bash
CORS_ALLOWED_ORIGINS=https://mp.dayilive.com,https://www.mp.dayilive.com,https://admin.mp.dayilive.com
```

### Q3: 开发环境可以访问生产 API 吗？

**A:** 可以！只要生产环境的 `CORS_ALLOWED_ORIGINS` 包含您的开发地址即可。但**不推荐**这样做，建议使用本地开发环境。

### Q4: 如何临时允许所有来源（仅开发）？

**A:** 修改 `main.py`：

```python
# ⚠️ 仅用于开发，生产环境不要使用！
origins = ["*"]  # 允许所有来源
```

**警告：** 生产环境**绝对不要**使用 `["*"]`，这会带来安全风险！

## 📝 修改记录

### 2025-01-XX 修复内容

1. ✅ 添加 `http://127.0.0.1:5174` 支持
2. ✅ 添加生产环境域名配置（环境变量）
3. ✅ 添加 `expose_headers` 配置
4. ✅ 支持多个生产域名（逗号分隔）

## ✅ 测试清单

- [ ] 本地开发：前端可以正常访问后端 API
- [ ] 本地开发：验证码接口可以正常调用
- [ ] 生产环境：环境变量正确设置
- [ ] 生产环境：前端可以正常访问后端 API
- [ ] 生产环境：多个域名都可以正常访问

---

**配置完成后，请重启后端服务！** 🚀

