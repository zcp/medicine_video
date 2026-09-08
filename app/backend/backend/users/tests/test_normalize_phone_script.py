"""
历史手机号清洗脚本单元测试 - test_normalize_phone_script.py
覆盖 app/scripts/normalize_phone_numbers.py（阶段 E 出口审查验收项）
主流程通过注入 sqlite 兼容模型 + 内存库进行真实执行验证，不依赖 postgres。
"""
import pytest
from sqlalchemy import BigInteger, Boolean, Column, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from app.scripts.normalize_phone_numbers import (
    classify_phone,
    mask_phone,
    scan_and_normalize,
)

TestBase = declarative_base()


class TestUser(TestBase):
    """测试用轻量模型，模拟 users 表结构（id/phone_number/is_phone_verified）"""

    __tablename__ = "test_users"

    id = Column(BigInteger, primary_key=True)
    phone_number = Column(String(20), unique=True)
    is_phone_verified = Column(Boolean, nullable=False, default=False)


@pytest.fixture
def session_engine():
    """内存 sqlite 会话（autoflush=False，与生产 SessionLocal 行为一致）+ 引擎"""
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    TestBase.metadata.create_all(engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    s = Session()
    yield s, engine
    s.close()


@pytest.fixture
def session(session_engine):
    return session_engine[0]


@pytest.fixture
def seeded(session):
    """预置典型脏数据场景

    u1: +86 前缀(可清洗)    u2: 86 前缀13位(与 u1 归一化后冲突, 需人工)
    u3: 空格分隔(可清洗)     u4: 横线分隔(可清洗)
    u5: 已归一化(跳过)       u6: 非法值(人工审核)
    u7: 未认证脏数据(不扫描)  u8: 空串(不扫描)
    """
    rows = [
        TestUser(id=1, phone_number="+8613800138000", is_phone_verified=True),
        TestUser(id=2, phone_number="8613800138000", is_phone_verified=True),
        TestUser(id=3, phone_number="137 0013 8000", is_phone_verified=True),
        TestUser(id=4, phone_number="139-1234-5678", is_phone_verified=True),
        TestUser(id=5, phone_number="13800138001", is_phone_verified=True),
        TestUser(id=6, phone_number="12345", is_phone_verified=True),
        TestUser(id=7, phone_number="+8613800138002", is_phone_verified=False),
        TestUser(id=8, phone_number="", is_phone_verified=True),
    ]
    session.add_all(rows)
    session.commit()
    return rows


class TestMaskPhone:
    """测试手机号打码"""

    def test_normal_length(self):
        assert mask_phone("13800138000") == "138****8000"

    def test_short_length(self):
        assert mask_phone("12345") == "*****"

    def test_empty(self):
        assert mask_phone("") == "(空)"


class TestClassifyPhone:
    """测试清洗分类"""

    def test_already_normalized(self):
        assert classify_phone("13800138000") == ("already", "")

    def test_plus86_prefix(self):
        assert classify_phone("+8613800138000") == ("normal", "13800138000")

    def test_86_prefix_13_digits(self):
        assert classify_phone("8613800138000") == ("normal", "13800138000")

    def test_spaces(self):
        assert classify_phone("138 0013 8000") == ("normal", "13800138000")

    def test_dashes(self):
        assert classify_phone("138-0013-8000") == ("normal", "13800138000")

    def test_invalid_short(self):
        assert classify_phone("12345678901") == ("invalid", "")

    def test_invalid_chars(self):
        assert classify_phone("abc") == ("invalid", "")

    def test_invalid_empty(self):
        assert classify_phone("") == ("invalid", "")


class TestScanAndNormalize:
    """测试主流程（sqlite 内存库真实执行）"""

    async_mode = False

    def _query_all(self, session_engine):
        """用独立只读会话查询库值，避免 identity map 返回内存脏对象"""
        from sqlalchemy import select
        from sqlalchemy.orm import Session as SaSession

        engine = session_engine[1]
        s = SaSession(bind=engine)
        try:
            return {
                row.id: row.phone_number
                for row in s.execute(select(TestUser)).scalars().all()
            }
        finally:
            s.close()

    def test_dry_run_no_write(self, seeded, session_engine):
        """预演：统计正确且不写库"""
        session = session_engine[0]
        stats, conflicts, invalids = scan_and_normalize(
            session, model=TestUser, execute=False, batch_size=2
        )
        assert stats["scanned"] == 6
        assert stats["already_normalized"] == 1
        assert stats["invalid"] == 1
        assert stats["conflict"] == 1
        assert stats["would_update"] == 3
        assert stats["updated"] == 0
        assert len(invalids) == 1 and invalids[0]["id"] == 6
        assert len(conflicts) == 1 and conflicts[0]["id"] == 2
        # 丢弃 dry-run 期间的未提交事务后，独立会话确认库内数据不变
        session.rollback()
        db = self._query_all(session_engine)
        assert db[1] == "+8613800138000"
        assert db[2] == "8613800138000"
        assert db[3] == "137 0013 8000"
        assert db[4] == "139-1234-5678"
        assert db[7] == "+8613800138002"

    def test_execute_normalizes(self, seeded, session_engine):
        """执行：脏格式归一化，冲突/非法/未认证/空串不动"""
        session = session_engine[0]
        stats, conflicts, invalids = scan_and_normalize(
            session, model=TestUser, execute=True, batch_size=2
        )
        assert stats["updated"] == 3
        assert stats["conflict"] == 1
        assert stats["invalid"] == 1
        db = self._query_all(session_engine)
        assert db[1] == "13800138000"
        assert db[2] == "8613800138000"
        assert db[3] == "13700138000"
        assert db[4] == "13912345678"
        assert db[5] == "13800138001"
        assert db[6] == "12345"
        assert db[7] == "+8613800138002"
        assert db[8] == ""

    def test_idempotent(self, seeded, session_engine):
        """幂等：执行后再预演无可清洗项"""
        session = session_engine[0]
        scan_and_normalize(session, model=TestUser, execute=True)
        stats, conflicts, invalids = scan_and_normalize(
            session, model=TestUser, execute=False
        )
        assert stats["would_update"] == 0
        # 冲突/非法属数据问题，需人工合并/审核；清洗可清理部分已归零，冲突与非法清单持续提示
        assert stats["conflict"] == 1
        assert stats["invalid"] == 1

    def test_limit(self, seeded, session_engine):
        """limit：仅扫描前 N 条"""
        session = session_engine[0]
        stats, conflicts, invalids = scan_and_normalize(
            session, model=TestUser, execute=False, limit=2
        )
        assert stats["scanned"] == 2
        assert stats["would_update"] == 1
        assert stats["conflict"] == 1
