"""
创建使用SHA256哈希的测试用户
"""
import sys
sys.path.append('/app')
import asyncio
import hashlib
from app.database import get_async_db
from app.models import User, UserRole, EntityStatus

def hash_password(password: str) -> str:
    """使用SHA256哈希密码"""
    return hashlib.sha256(password.encode()).hexdigest()

async def create_test_users():
    try:
        async for db in get_async_db():
            # 删除现有的测试用户
            from sqlalchemy import text
            await db.execute(text('DELETE FROM users WHERE username IN (:user1, :user2)'), 
                           {'user1': 'test_user', 'user2': 'test_admin'})
            
            # 创建测试用户
            test_user = User(
                username="test_user",
                nickname="测试用户",
                email="test@example.com",
                password_hash=hash_password("test123"),
                role=UserRole.REGULAR,
                status=EntityStatus.NORMAL,
                is_email_verified=True
            )
            
            test_admin = User(
                username="test_admin", 
                nickname="测试管理员",
                email="admin@test.com",
                password_hash=hash_password("admin123"),
                role=UserRole.ADMIN,
                status=EntityStatus.NORMAL,
                is_email_verified=True
            )
            
            db.add(test_user)
            db.add(test_admin)
            await db.commit()
            
            print("=== 测试用户创建成功 ===")
            print("普通用户:")
            print(f"  用户名: test_user")
            print(f"  密码: test123")
            print(f"  SHA256哈希: {hash_password('test123')}")
            print()
            print("管理员:")
            print(f"  用户名: test_admin")
            print(f"  密码: admin123") 
            print(f"  SHA256哈希: {hash_password('admin123')}")
            
            break
            
    except Exception as e:
        print(f"创建用户失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_test_users())
