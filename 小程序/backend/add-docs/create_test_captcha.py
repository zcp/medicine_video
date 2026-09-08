"""
创建测试验证码的脚本
"""
import asyncio
import uuid
import sys
import os

# 添加app路径
sys.path.append('/app')

async def create_test_captcha():
    try:
        from app.core.redis_client import get_redis_client
        
        redis_client = await get_redis_client()
        
        # 生成5位数字验证码
        import random
        captcha_text = ''.join([str(random.randint(0, 9)) for _ in range(5)])  # 5位随机数字
        captcha_id = str(uuid.uuid4())
        
        # 存储到Redis（10分钟过期）
        cache_key = f"captcha:solution:{captcha_id}"
        await redis_client.setex(cache_key, 600, captcha_text.lower())
        
        print("=== 测试验证码信息 ===")
        print(f"验证码ID: {captcha_id}")
        print(f"验证码答案: {captcha_text}")
        print()
        print("=== 登录JSON ===")
        print("普通用户登录:")
        print("{")
        print('  "username": "test_user",')
        print('  "password": "test123",')
        print(f'  "captcha_id": "{captcha_id}",')
        print(f'  "captcha_solution": "{captcha_text}"')
        print("}")
        print()
        print("管理员登录:")
        print("{")
        print('  "username": "test_admin",')
        print('  "password": "admin123",')
        print(f'  "captcha_id": "{captcha_id}",')
        print(f'  "captcha_solution": "{captcha_text}"')
        print("}")
        print()
        print("=== API地址 ===")
        print("POST http://localhost:8002/api/v1/auth/login")
        print("或")
        print("POST http://localhost:8080/api/users/auth/login")
        
        await redis_client.close()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_test_captcha())
