"""
测试 DateTime vs TIMESTAMP 在PostgreSQL中的映射差异
"""

from sqlalchemy import create_engine, Column, DateTime, TIMESTAMP, MetaData, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

# 创建测试引擎（使用内存数据库进行演示）
engine = create_engine('postgresql://user:pass@localhost/test', echo=True)

Base = declarative_base()

class TestDateTime(Base):
    """使用 DateTime 的测试表"""
    __tablename__ = 'test_datetime'
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

class TestTimestamp(Base):
    """使用 TIMESTAMP 的测试表"""
    __tablename__ = 'test_timestamp'
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

# 生成DDL语句来查看实际映射
def generate_ddl():
    """生成DDL语句来查看实际映射"""
    print("=== DateTime 映射的DDL ===")
    ddl_datetime = TestDateTime.__table__.compile(engine)
    print(ddl_datetime)
    
    print("\n=== TIMESTAMP 映射的DDL ===")
    ddl_timestamp = TestTimestamp.__table__.compile(engine)
    print(ddl_timestamp)

if __name__ == "__main__":
    generate_ddl() 