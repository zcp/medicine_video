"""
DateTime vs TIMESTAMP 详细对比测试
演示在PostgreSQL中的实际差异
"""

from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, DateTime, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class DateTimeTest(Base):
    """使用 DateTime 的测试"""
    __tablename__ = 'datetime_test'
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

class TimestampTest(Base):
    """使用 TIMESTAMP 的测试"""
    __tablename__ = 'timestamp_test'
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

def demonstrate_differences():
    """演示两种类型的差异"""
    
    print("=== SQLAlchemy 类型映射差异 ===\n")
    
    print("1. DateTime(timezone=True) 在PostgreSQL中映射为:")
    print("   TIMESTAMP WITHOUT TIME ZONE")
    print("   - 不存储时区信息")
    print("   - 可能导致时区歧义")
    print("   - 不完全匹配 TIMESTAMPTZ\n")
    
    print("2. TIMESTAMP(timezone=True) 在PostgreSQL中映射为:")
    print("   TIMESTAMP WITH TIME ZONE (TIMESTAMPTZ)")
    print("   - 存储完整的时区信息")
    print("   - 正确处理时区转换")
    print("   - 完全匹配设计文档中的 TIMESTAMPTZ\n")
    
    print("=== 实际影响示例 ===\n")
    
    print("场景: 跨时区应用")
    print("用户在北京 (UTC+8) 创建记录")
    print("服务器在纽约 (UTC-5) 处理数据\n")
    
    print("使用 DateTime(timezone=True):")
    print("- 存储: 2024-01-01 10:00:00")
    print("- 问题: 不知道这个时间是哪个时区的")
    print("- 风险: 可能产生13小时的时差错误\n")
    
    print("使用 TIMESTAMP(timezone=True):")
    print("- 存储: 2024-01-01 10:00:00+08:00")
    print("- 优势: 明确知道这是北京时间")
    print("- 结果: 正确处理时区转换\n")
    
    print("=== 设计文档一致性 ===\n")
    
    print("原始DDL设计:")
    print("created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP\n")
    
    print("正确的SQLAlchemy映射:")
    print("created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())\n")
    
    print("不正确的映射:")
    print("created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())\n")
    
    print("=== 推荐做法 ===\n")
    
    print("✅ 在PostgreSQL环境中，始终使用:")
    print("   TIMESTAMP(timezone=True) 来映射 TIMESTAMPTZ")
    print("   这样可以确保:")
    print("   - 时区信息完整性")
    print("   - 跨时区应用的正确性")
    print("   - 与设计文档的一致性")

if __name__ == "__main__":
    demonstrate_differences() 