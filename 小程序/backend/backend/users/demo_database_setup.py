#!/usr/bin/env python3
"""
数据库设置演示脚本

该脚本演示如何使用数据库初始化功能并插入一些示例数据。
仅用于开发和测试环境。
"""

import logging
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def demo_database_setup():
    """
    演示数据库设置和数据插入
    """
    try:
        logger.info("🚀 开始数据库设置演示...")
        
        # 1. 初始化数据库表
        logger.info("1️⃣ 初始化数据库表...")
        from app.scripts.create_tables import init_db
        
        if not init_db():
            logger.error("数据库初始化失败")
            return False
        
        # 2. 导入必要的模块
        from app.database import SessionLocal
        from app.models import (
            User, MembershipProduct, UserMembership,
            UserRole, EntityStatus, MembershipProductStatus, MembershipStatus
        )
        
        # 3. 创建示例数据
        logger.info("2️⃣ 插入示例数据...")
        
        with SessionLocal() as session:
            # 创建会员产品
            products = [
                MembershipProduct(
                    code="BASIC_MONTHLY",
                    name="基础月度会员",
                    description="基础功能，月度订阅",
                    price=Decimal("29.99"),
                    level=1,
                    duration_unit="month",
                    duration_value=1,
                    status=MembershipProductStatus.ACTIVE
                ),
                MembershipProduct(
                    code="PREMIUM_YEARLY", 
                    name="高级年度会员",
                    description="全功能，年度优惠",
                    price=Decimal("299.99"),
                    level=2,
                    duration_unit="year",
                    duration_value=1,
                    status=MembershipProductStatus.ACTIVE
                )
            ]
            
            for product in products:
                session.add(product)
            
            # 创建示例用户
            users = [
                User(
                    username="demo_user",
                    nickname="演示用户",
                    email="demo@example.com",
                    password_hash="$2b$12$demo_hashed_password",
                    role=UserRole.REGULAR,
                    status=EntityStatus.NORMAL,
                    is_email_verified=True
                ),
                User(
                    username="admin_user",
                    nickname="管理员",
                    email="admin@example.com", 
                    password_hash="$2b$12$admin_hashed_password",
                    role=UserRole.ADMIN,
                    status=EntityStatus.NORMAL,
                    is_email_verified=True
                )
            ]
            
            for user in users:
                session.add(user)
            
            # 提交更改以获取用户ID
            session.commit()
            
            # 为演示用户创建会员订阅
            demo_user = session.query(User).filter_by(username="demo_user").first()
            if demo_user:
                membership = UserMembership(
                    user_id=demo_user.id,
                    product_code="BASIC_MONTHLY",
                    level=1,
                    status=MembershipStatus.ACTIVE,
                    is_auto_renew=True,
                    start_date=datetime.now(),
                    expires_at=datetime.now() + timedelta(days=30)
                )
                session.add(membership)
            
            session.commit()
            
        logger.info("3️⃣ 验证数据插入...")
        
        # 验证数据
        with SessionLocal() as session:
            user_count = session.query(User).count()
            product_count = session.query(MembershipProduct).count()
            membership_count = session.query(UserMembership).count()
            
            logger.info(f"   - 用户数量: {user_count}")
            logger.info(f"   - 产品数量: {product_count}")
            logger.info(f"   - 订阅数量: {membership_count}")
            
            # 显示具体数据
            logger.info("   - 用户列表:")
            for user in session.query(User).all():
                logger.info(f"     * {user.username} ({user.nickname}) - {user.role.value}")
            
            logger.info("   - 产品列表:")
            for product in session.query(MembershipProduct).all():
                logger.info(f"     * {product.code}: {product.name} - ¥{product.price}")
        
        logger.info("✅ 数据库设置演示完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 演示失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def clean_demo_data():
    """
    清理演示数据
    """
    try:
        logger.info("🧹 清理演示数据...")
        
        from app.database import SessionLocal
        from app.models import User, MembershipProduct, UserMembership
        
        with SessionLocal() as session:
            # 删除演示数据（按顺序删除以避免外键约束错误）
            session.query(UserMembership).delete()
            session.query(User).filter(User.username.in_(["demo_user", "admin_user"])).delete()
            session.query(MembershipProduct).filter(
                MembershipProduct.code.in_(["BASIC_MONTHLY", "PREMIUM_YEARLY"])
            ).delete()
            session.commit()
        
        logger.info("✅ 演示数据清理完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 清理失败: {str(e)}")
        return False


def main():
    """
    主函数
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库设置演示')
    parser.add_argument('--clean', action='store_true', help='清理演示数据')
    
    args = parser.parse_args()
    
    if args.clean:
        success = clean_demo_data()
    else:
        success = demo_database_setup()
    
    if success:
        logger.info("🎉 操作成功完成！")
        sys.exit(0)
    else:
        logger.error("💥 操作失败！")
        sys.exit(1)


if __name__ == "__main__":
    main() 