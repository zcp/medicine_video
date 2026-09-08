import sys
sys.path.append('/app')
import asyncio
import bcrypt
from app.database import get_async_db
from app.models import User
from sqlalchemy import select

async def check_password():
    async for db in get_async_db():
        # 使用ORM查询
        stmt = select(User).where(User.username == 'test_admin')
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            print(f'用户: {user.username}')
            print(f'密码哈希: {user.password_hash}')
            
            # 验证密码
            password = 'admin123'
            try:
                is_valid = bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8'))
                print(f'密码 "{password}" 验证结果: {is_valid}')
            except Exception as e:
                print(f'密码验证错误: {e}')
        else:
            print('用户不存在')
        break

if __name__ == "__main__":
    asyncio.run(check_password())
