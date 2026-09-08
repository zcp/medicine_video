#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""临时脚本：修复 .env.example 文件编码"""

content = """# ============================================
# LiveCore Service 环境变量配置模板
# ============================================
# 
# 使用说明:
# 1. 复制此文件为 .env: cp .env.example .env
# 2. 根据实际环境填写配置值
# 3. 生产环境必须设置所有必需变量
# 4. 不要将 .env 文件提交到版本控制系统
#
# ============================================

# ========== 环境标识 ==========
# 可选值: development, staging, production
ENVIRONMENT=development

# ========== 数据库配置 ==========
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=live_core_test
POSTGRES_USER=postgres
# ⚠️ 生产环境必须设置强密码（不要使用默认值）
POSTGRES_PASSWORD=your_secure_password_here

# ========== CORS配置 ==========
# 开发环境示例: CORS_ORIGINS=http://localhost:5175,http://localhost:3000
# 生产环境示例: CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
# ⚠️ 生产环境不要使用 * （通配符）
CORS_ORIGINS=*

# ========== JWT配置 ==========
# ⚠️ 生产环境必须设置强密钥（推荐64字符以上）
# 生成方式: openssl rand -hex 32
JWT_SECRET_KEY=your_jwt_secret_key_here_min_32_chars
JWT_ALGORITHM=HS256

# ========== Celery配置 ==========
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# ========== 应用配置 ==========
DEBUG=true
ROOM_MEDIA_ROOT_PATH=./media
UPLOAD_MAX_SIZE=10485760
UPLOAD_ALLOWED_EXTENSIONS=jpg,jpeg,png,gif
PLAYBACK_BASE_URL=http://localhost:8000
"""

if __name__ == "__main__":
    with open('.env.example', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Success: .env.example created with UTF-8 encoding")

