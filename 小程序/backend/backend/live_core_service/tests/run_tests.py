#!/usr/bin/env python3
"""
简单的测试运行脚本
用于验证生成的测试代码是否可以正确导入和运行
"""

import sys
import os

# 添加项目根目录到Python路径
# 当前文件在 tests/ 目录下，需要向上一级到 live_core_service/ 目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_imports():
    """测试所有测试模块是否可以正确导入"""
    try:
        # 测试conftest导入
        from tests.conftest import db_session, sync_client, async_client
        print("✅ conftest.py 导入成功")
        
        # 测试CRUD单元测试导入
        from tests.unit.test_crud_room import (
            test_create_room, test_get_room, test_update_room, 
            test_remove_room, test_is_live_true
        )
        print("✅ test_crud_room.py 导入成功")
        
        # 测试API集成测试导入
        from tests.integration.test_api_room import (
            test_create_room_success, test_get_room_success, 
            test_update_room_success, test_delete_room_success
        )
        print("✅ test_api_room.py 导入成功")
        
        print("\n🎉 所有测试模块导入成功！")
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

def main():
    """主函数"""
    print("=== 测试代码验证 ===")
    print("正在检查测试模块导入...")
    
    if test_imports():
        print("\n✅ 测试代码生成成功！")
        print("\n📝 运行测试的命令:")
        print("  pytest tests/unit/test_crud_room.py -v")
        print("  pytest tests/integration/test_api_room.py -v")
        print("  pytest tests/ -v  # 运行所有测试")
    else:
        print("\n❌ 测试代码存在问题，请检查导入错误")
        sys.exit(1)

if __name__ == "__main__":
    main() 