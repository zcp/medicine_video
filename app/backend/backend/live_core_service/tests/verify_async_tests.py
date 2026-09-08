#!/usr/bin/env python3
"""
验证异步测试修改的脚本
检查所有API测试函数是否正确修改为异步
"""

import ast
import sys
import os

def check_async_tests():
    """检查测试文件中的函数是否都是异步的"""
    test_file = "tests/integration/test_api_room.py"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return False
    
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"❌ 语法错误: {e}")
        return False
    
    test_functions = []
    async_functions = []
    decorated_functions = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name.startswith('test_'):
                test_functions.append(node.name)
                
                # 检查是否是异步函数
                if isinstance(node, ast.AsyncFunctionDef):
                    async_functions.append(node.name)
                
                # 检查是否有pytest.mark.asyncio装饰器
                for decorator in node.decorator_list:
                    if (isinstance(decorator, ast.Attribute) and 
                        isinstance(decorator.value, ast.Attribute) and
                        decorator.value.attr == 'mark' and
                        decorator.attr == 'asyncio'):
                        decorated_functions.append(node.name)
    
    print("=== 异步测试验证结果 ===")
    print(f"发现测试函数: {len(test_functions)}个")
    print(f"异步函数: {len(async_functions)}个")
    print(f"带装饰器的函数: {len(decorated_functions)}个")
    
    # 检查是否所有测试函数都是异步的
    non_async = set(test_functions) - set(async_functions)
    if non_async:
        print(f"❌ 以下测试函数不是异步的: {non_async}")
        return False
    
    # 检查是否所有测试函数都有装饰器
    non_decorated = set(test_functions) - set(decorated_functions)
    if non_decorated:
        print(f"❌ 以下测试函数缺少@pytest.mark.asyncio装饰器: {non_decorated}")
        return False
    
    print("✅ 所有测试函数都正确修改为异步!")
    
    # 检查是否使用了async_client
    if 'sync_client' in content:
        print("❌ 代码中仍然存在sync_client的引用")
        return False
    
    if 'async_client' not in content:
        print("❌ 代码中没有找到async_client的引用")
        return False
    
    print("✅ 客户端参数修改正确!")
    
    # 检查是否有await关键字
    await_count = content.count('await ')
    if await_count < 20:  # 应该有很多await调用
        print(f"⚠️ await调用次数可能不够: {await_count}")
    else:
        print(f"✅ 找到{await_count}个await调用")
    
    return True

if __name__ == "__main__":
    success = check_async_tests()
    if success:
        print("\n🎉 异步测试修改验证通过!")
    else:
        print("\n❌ 异步测试修改验证失败!")
        sys.exit(1) 