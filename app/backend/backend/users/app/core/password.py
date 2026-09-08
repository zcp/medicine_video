"""
密码工具模块 —— 提供安全的密码哈希与验证能力

- 使用 bcrypt 作为默认哈希算法
- 向下兼容旧版 SHA-256 哈希，支持老用户平滑迁移
- AuthService 与 UserService 共用，确保一致性
"""
import hashlib

import bcrypt


def hash_password(password: str) -> str:
    """使用 bcrypt 哈希密码"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码，兼容旧 SHA-256 哈希与新版 bcrypt 哈希"""
    if not password or not password_hash:
        return False

    # bcrypt 哈希以 $2b$ 或 $2a$ 开头
    if password_hash.startswith("$2b$") or password_hash.startswith("$2a$"):
        return bcrypt.checkpw(password.encode(), password_hash.encode())

    # 旧版 SHA-256：64 位十六进制字符串
    if len(password_hash) == 64 and all(c in "0123456789abcdef" for c in password_hash.lower()):
        return hashlib.sha256(password.encode()).hexdigest() == password_hash

    return False


def is_legacy_sha256_hash(password_hash: str) -> bool:
    """判断是否为旧版 SHA-256 哈希"""
    if not password_hash:
        return False

    return (
        len(password_hash) == 64
        and all(c in "0123456789abcdef" for c in password_hash.lower())
        and not password_hash.startswith("$2b$")
        and not password_hash.startswith("$2a$")
    )
