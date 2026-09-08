"""为指定用户名创建 public_id（如果缺失）

使用方法：在能访问 users 数据库的环境中运行（例如 users 服务容器内或主机上）。

示例：
  pip install psycopg2-binary
  python create_public_id_for_admin.py --host localhost --port 5432 --db users_service_test --user postgres --password 324zq999 --username test_admin

脚本会查询用户名对应的记录，若 `public_id` 为空则生成 UUID 并写入。
"""
import argparse
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--host', default='localhost')
    p.add_argument('--port', default=5432, type=int)
    p.add_argument('--user', default='postgres')
    p.add_argument('--password', default='')
    p.add_argument('--db', default='users_service_test')
    p.add_argument('--username', default='test_admin')
    args = p.parse_args()

    conn = psycopg2.connect(host=args.host, port=args.port, user=args.user, password=args.password, dbname=args.db)
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, public_id, username FROM users WHERE username = %s", (args.username,))
                row = cur.fetchone()
                if not row:
                    print(f"用户 {args.username} 未找到（数据库: {args.db}）。")
                    return

                if row.get('public_id'):
                    print(f"用户 {args.username} 已有 public_id: {row['public_id']}")
                    return

                new_pub = str(uuid.uuid4())
                cur.execute("UPDATE users SET public_id = %s WHERE id = %s", (new_pub, row['id']))
                print(f"已为用户 {args.username} 创建 public_id: {new_pub}")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
