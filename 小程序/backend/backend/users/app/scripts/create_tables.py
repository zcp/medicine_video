#!/usr/bin/env python3
"""
数据库表初始化脚本

该脚本用于根据 SQLAlchemy 模型定义创建数据库表。
运行方式：
  python -m app.scripts.create_tables  (从 users/ 根目录运行)
"""

import logging
import sys
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def init_db():
    """
    初始化数据库，创建所有表
    """
    try:
        logger.info("开始初始化数据库...")
        
        # 导入数据库连接和基类
        from app.database import engine, Base
        logger.info("成功导入数据库引擎和基类")
        
        # 显式导入所有模型类以确保它们被注册到元数据中
        # 这是关键步骤，否则 create_all 可能不会创建任何表
        from app.models.users import (
            User, 
            MembershipProduct, 
            UserMembership,
            UserRole,
            EntityStatus,
            MembershipProductStatus,
            MembershipStatus
        )
        logger.info("成功导入所有模型类")
        
        # 显示将要创建的表
        tables_to_create = list(Base.metadata.tables.keys())
        if tables_to_create:
            logger.info(f"将要创建以下数据库表: {', '.join(tables_to_create)}")
        else:
            logger.warning("未发现任何需要创建的表，请检查模型定义")
            return False
        
        # 创建所有表
        logger.info("开始创建数据库表...")
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ 数据库表创建成功！")
        
        # 验证创建的表
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        logger.info(f"数据库中现有表: {', '.join(existing_tables)}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ 导入模块失败: {str(e)}")
        logger.error("请确保在项目根目录 (users/) 下运行此脚本")
        return False
        
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {str(e)}")
        logger.error("可能的原因:")
        logger.error("1. 数据库连接配置错误")
        logger.error("2. 数据库服务未启动")
        logger.error("3. 数据库权限不足")
        logger.error("4. 模型定义存在错误")
        return False


def drop_all_tables():
    """
    删除所有表（危险操作，仅用于开发环境）
    """
    try:
        logger.warning("⚠️  开始删除所有数据库表...")
        
        from app.database import engine, Base
        from app.models.users import User, MembershipProduct, UserMembership
        
        # 确认操作
        confirm = input("确定要删除所有表吗？这将清除所有数据！(输入 'yes' 确认): ")
        if confirm.lower() != 'yes':
            logger.info("操作已取消")
            return False
        
        Base.metadata.drop_all(bind=engine)
        logger.info("✅ 所有表已删除")
        return True
        
    except Exception as e:
        logger.error(f"❌ 删除表失败: {str(e)}")
        return False


def main():
    """
    主函数：提供命令行参数支持
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库表管理工具')
    parser.add_argument(
        '--drop', 
        action='store_true', 
        help='删除所有表（危险操作）'
    )
    
    args = parser.parse_args()
    
    if args.drop:
        success = drop_all_tables()
        if success:
            # 删除成功后重新创建表
            logger.info("开始重新创建表...")
            success = init_db()
    else:
        success = init_db()
    
    if success:
        logger.info("🎉 操作完成！")
        sys.exit(0)
    else:
        logger.error("💥 操作失败！")
        sys.exit(1)


if __name__ == "__main__":
    main() 