#!/usr/bin/env python3
"""
应用启动测试
验证main.py是否可以正常导入和启动
"""

def test_app_import():
    """测试应用导入"""
    try:
        from app.main import app
        print("✅ 应用导入成功")
        
        # 检查路由
        routes = [route.path for route in app.routes]
        print(f"✅ 发现路由: {routes}")
        
        return True
    except Exception as e:
        print(f"❌ 应用导入失败: {e}")
        return False

def test_config_import():
    """测试配置导入"""
    try:
        from app.core.config import settings
        print(f"✅ 配置导入成功")
        print(f"项目名称: {settings.PROJECT_NAME}")
        print(f"API前缀: {settings.API_V1_STR}")
        return True
    except Exception as e:
        print(f"❌ 配置导入失败: {e}")
        return False

if __name__ == "__main__":
    print("=== 应用启动测试 ===")
    
    config_ok = test_config_import()
    app_ok = test_app_import()
    
    if config_ok and app_ok:
        print("\n🎉 应用启动测试通过!")
    else:
        print("\n❌ 应用启动测试失败!")
        exit(1) 