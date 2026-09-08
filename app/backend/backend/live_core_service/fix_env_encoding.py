#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修复 .env 文件编码问题"""

import sys

def fix_env_file():
    """修复 .env 文件编码"""
    env_file = '.env'
    
    # 尝试读取文件，检测编码问题
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
    content = None
    used_encoding = None
    
    for encoding in encodings:
        try:
            with open(env_file, 'r', encoding=encoding) as f:
                content = f.read()
            used_encoding = encoding
            print(f"Success: Read file using {encoding} encoding")
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Error reading file ({encoding}): {e}")
            return False
    
    if content is None:
        print("Error: Cannot read .env file, please check if file exists")
        return False
    
    # 如果文件不是UTF-8编码，重新保存为UTF-8
    if used_encoding != 'utf-8':
        print(f"Warning: File encoding is {used_encoding}, converting to UTF-8")
        try:
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("Success: File converted to UTF-8 encoding")
        except Exception as e:
            print(f"Error saving file: {e}")
            return False
    else:
        print("Success: File is already UTF-8 encoded, no changes needed")
    
    # 验证文件可以正常读取
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"Verification passed: File contains {len(lines)} lines")
        return True
    except Exception as e:
        print(f"Verification failed: {e}")
        return False

if __name__ == "__main__":
    success = fix_env_file()
    sys.exit(0 if success else 1)
