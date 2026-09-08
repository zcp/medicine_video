#!/usr/bin/env python3
"""
简单的导入测试脚本
验证 SQLAlchemy 模型和 Pydantic Schema 是否能正确导入
"""

def test_models_import():
    """测试 SQLAlchemy 模型导入"""
    try:
        from app.models import (
            Base, User, MembershipProduct, UserMembership,
            UserRole, EntityStatus, MembershipProductStatus, MembershipStatus
        )
        print("✅ SQLAlchemy 模型导入成功")
        print(f"   - 用户模型: {User.__name__}")
        print(f"   - 会员产品模型: {MembershipProduct.__name__}")
        print(f"   - 用户会员订阅模型: {UserMembership.__name__}")
        print(f"   - 用户角色枚举: {UserRole.__name__}")
        
        # 测试 Base 是否来自正确的源
        from app.database import Base as DatabaseBase
        if Base is DatabaseBase:
            print("   - Base 对象引用正确")
        else:
            print("   - ⚠️ Base 对象引用可能有问题")
        
        return True
    except ImportError as e:
        print(f"❌ SQLAlchemy 模型导入失败: {e}")
        return False


def test_schemas_import():
    """测试 Pydantic Schema 导入"""
    try:
        from app.schemas import (
            UserCreate, UserUpdate, UserResponse,
            MembershipProductCreate, MembershipProductResponse,
            UserMembershipCreate, UserMembershipResponse,
            PaginatedUsersResponse
        )
        print("✅ Pydantic Schema 导入成功")
        print(f"   - 用户创建 Schema: {UserCreate.__name__}")
        print(f"   - 用户响应 Schema: {UserResponse.__name__}")
        print(f"   - 会员产品创建 Schema: {MembershipProductCreate.__name__}")
        print(f"   - 用户会员订阅响应 Schema: {UserMembershipResponse.__name__}")
        return True
    except ImportError as e:
        print(f"❌ Pydantic Schema 导入失败: {e}")
        return False


def test_enum_values():
    """测试枚举值"""
    try:
        from app.models import UserRole, EntityStatus, MembershipStatus
        
        print("✅ 枚举值测试:")
        print(f"   - 用户角色: {[role.value for role in UserRole]}")
        print(f"   - 实体状态: {[status.value for status in EntityStatus]}")
        print(f"   - 会员状态: {[status.value for status in MembershipStatus]}")
        return True
    except Exception as e:
        print(f"❌ 枚举值测试失败: {e}")
        return False


if __name__ == "__main__":
    print("🚀 开始测试用户功能服务的模型和 Schema 导入...")
    print("=" * 60)
    
    success_count = 0
    total_tests = 3
    
    if test_models_import():
        success_count += 1
    print()
    
    if test_schemas_import():
        success_count += 1
    print()
    
    if test_enum_values():
        success_count += 1
    print()
    
    print("=" * 60)
    print(f"📊 测试结果: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("🎉 所有导入测试通过！代码生成成功。")
        exit(0)
    else:
        print("⚠️ 部分测试失败，请检查导入路径和代码结构。")
        exit(1) 