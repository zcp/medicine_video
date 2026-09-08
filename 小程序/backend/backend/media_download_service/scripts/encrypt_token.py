#!/usr/bin/env python3
"""
Token加密工具

用法:
1. 生成密钥: python scripts/encrypt_token.py --generate-key
2. 加密token: python scripts/encrypt_token.py "your_token_here"
3. 解密验证: python scripts/encrypt_token.py --decrypt "encrypted_token" "encryption_key"
"""
import sys
from cryptography.fernet import Fernet


def generate_key():
    """生成新的加密密钥"""
    key = Fernet.generate_key()
    print("=" * 60)
    print("✅ 生成的加密密钥:")
    print(key.decode())
    print("=" * 60)
    print("\n💡 使用说明:")
    print("1. 将此密钥保存到环境变量 TOKEN_ENCRYPTION_KEY")
    print("2. 使用此密钥加密token: python encrypt_token.py <token> <key>")
    print("=" * 60)
    return key


def encrypt_token(token: str, key: str):
    """加密token"""
    cipher = Fernet(key.encode())
    encrypted = cipher.encrypt(token.encode())
    print("=" * 60)
    print("✅ 加密后的Token:")
    print(encrypted.decode())
    print("=" * 60)
    print("\n💡 使用说明:")
    print("将加密后的Token保存到环境变量 VZAN_TOKEN")
    print("=" * 60)
    return encrypted.decode()


def decrypt_token(encrypted_token: str, key: str):
    """解密token（用于验证）"""
    try:
        cipher = Fernet(key.encode())
        decrypted = cipher.decrypt(encrypted_token.encode())
        print("=" * 60)
        print("✅ 解密成功!")
        print("原始Token:")
        print(decrypted.decode())
        print("=" * 60)
        return decrypted.decode()
    except Exception as e:
        print("=" * 60)
        print(f"❌ 解密失败: {str(e)}")
        print("=" * 60)
        return None


def main():
    """主函数：解析命令行参数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  1. 生成密钥: python encrypt_token.py --generate-key")
        print("  2. 加密token: python encrypt_token.py <token> [encryption_key]")
        print("  3. 解密验证: python encrypt_token.py --decrypt <encrypted_token> <encryption_key>")
        sys.exit(1)
    
    if sys.argv[1] == '--generate-key':
        generate_key()
    
    elif sys.argv[1] == '--decrypt':
        if len(sys.argv) != 4:
            print("错误: --decrypt 需要2个参数")
            print("用法: python encrypt_token.py --decrypt <encrypted_token> <encryption_key>")
            sys.exit(1)
        decrypt_token(sys.argv[2], sys.argv[3])
    
    else:
        # 加密token
        token = sys.argv[1]
        
        if len(sys.argv) == 3:
            key = sys.argv[2]
        else:
            print("未提供加密密钥，自动生成新密钥...")
            key = generate_key().decode()
            print()
        
        encrypt_token(token, key)


if __name__ == "__main__":
    main()

