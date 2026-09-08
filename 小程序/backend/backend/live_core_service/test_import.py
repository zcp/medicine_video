"""
简单的导入测试文件
用于验证生成的代码是否可以正确导入
"""

try:
    # 测试CRUD模块导入
    from app.crud import room as crud_room
    print("✅ CRUD模块导入成功")
    
    # 测试API端点模块导入
    from app.api.v1.endpoints import room as room_endpoints
    print("✅ API端点模块导入成功")
    
    # 测试Schema模块导入
    from app.schemas.live_core import LiveRoomCreate, LiveRoomUpdate, LiveRoomResponse
    print("✅ Schema模块导入成功")
    
    # 测试Model模块导入
    from app.models.live_core import LiveRoom, LiveSession, SessionStatistics
    print("✅ Model模块导入成功")
    
    # 测试数据库模块导入
    from app.database import get_db, Base
    print("✅ 数据库模块导入成功")
    
    print("\n🎉 所有模块导入测试通过！")
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
except Exception as e:
    print(f"❌ 其他错误: {e}") 