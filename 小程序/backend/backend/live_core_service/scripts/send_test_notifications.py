"""向数据库插入测试通知脚本

用法：直接运行脚本，它会尝试查找用户名为 `test_user` 和 `test_admin` 的 public_id，
并为找到的用户各插入两条测试通知。如果未找到用户，请以命令行参数传入目标 user_id（UUID）。
"""
import sys
import asyncio
import uuid
from typing import List

sys.path.append('.')

from app.database import get_async_db
from app.crud.user_preference_notification import bulk_create_notifications


async def find_user_public_ids(db) -> List[str]:
    # 尝试查找 test_user 和 test_admin 的 public_id（如果 users 表在同一DB）
    try:
        rows = await db.execute("SELECT public_id, username FROM users WHERE username IN ('test_user','test_admin')")
        found = rows.fetchall()
        return [str(r[0]) for r in found]
    except Exception:
        return []


async def main():
    # 如果用户通过命令行提供 user_id（可以提供多个），优先使用
    provided_ids = sys.argv[1:]

    async for db in get_async_db():
        target_ids = []

        if provided_ids:
            target_ids = provided_ids
        else:
            target_ids = await find_user_public_ids(db)

        if not target_ids:
            print("未找到目标用户，请传入 user_id 参数，或先创建 test_user/test_admin。示例: python send_test_notifications.py <user_uuid>")
            return

        notifications = []
        for uid in target_ids:
            notifications.append({
                'user_id': uid,
                'title': '测试通知 — 欢迎',
                'content': '这是一条用于前端测试的系统通知（1）。',
                'notification_type': 'system',
                'related_id': None,
                'related_type': None,
                'is_read': False
            })
            notifications.append({
                'user_id': uid,
                'title': '测试通知 — 操作提醒',
                'content': '这是一条用于前端测试的系统通知（2）。',
                'notification_type': 'interaction',
                'related_id': None,
                'related_type': None,
                'is_read': False
            })

        count = await bulk_create_notifications(db, notifications)
        print(f"已插入 {count} 条测试通知，目标用户: {', '.join(target_ids)}")


if __name__ == '__main__':
    asyncio.run(main())
