"""
内容管理模块 Schema 层单元测试（纯 Pydantic 校验，无 DB 依赖）

覆盖标签管理 V2 的 Schema 契约：
- SessionTagsSetRequest：tag_ids 0~5、空列表合法、去重校验
- TagResolveRequest：strip / 非空 / 特殊字符 / 长度校验
- TagResolveResponse：默认信封
"""
import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.content_management import (
    SessionTagsSetRequest,
    TagResolveData,
    TagResolveRequest,
    TagResolveResponse,
)


# ============================================================================
# SessionTagsSetRequest — tag_ids 0～5
# ============================================================================

class TestSessionTagsSetRequestLimits:
    def test_empty_list_allowed_replace(self):
        """replace 传空列表 = 清空，应合法（V2 放开 0）"""
        req = SessionTagsSetRequest(tag_ids=[], mode="replace")
        assert req.tag_ids == []
        assert req.mode == "replace"

    def test_empty_list_allowed_append(self):
        """append 传空列表也应合法（无新增）"""
        req = SessionTagsSetRequest(tag_ids=[], mode="append")
        assert req.tag_ids == []

    def test_five_ids_allowed(self):
        """5 个 id = 上限，合法"""
        ids = [uuid.uuid4() for _ in range(5)]
        req = SessionTagsSetRequest(tag_ids=ids, mode="replace")
        assert len(req.tag_ids) == 5

    def test_six_ids_rejected(self):
        """6 个 id 超上限，应 422（ValidationError）"""
        ids = [uuid.uuid4() for _ in range(6)]
        with pytest.raises(ValidationError):
            SessionTagsSetRequest(tag_ids=ids, mode="replace")

    def test_duplicate_ids_rejected(self):
        """列表内重复 id 应拒绝"""
        tid = uuid.uuid4()
        with pytest.raises(ValidationError):
            SessionTagsSetRequest(tag_ids=[tid, tid], mode="replace")

    def test_invalid_mode_rejected(self):
        """mode 仅允许 replace|append"""
        with pytest.raises(ValidationError):
            SessionTagsSetRequest(tag_ids=[], mode="merge")


# ============================================================================
# TagResolveRequest — name 校验
# ============================================================================

class TestTagResolveRequestName:
    def test_strip_name(self):
        """前后空白应被 strip"""
        req = TagResolveRequest(name="  腹腔镜肝切除  ")
        assert req.name == "腹腔镜肝切除"

    def test_blank_name_rejected(self):
        """strip 后为空应拒绝"""
        with pytest.raises(ValidationError):
            TagResolveRequest(name="   ")

    def test_special_chars_rejected(self):
        """特殊字符 < > ' \" ; 应拒绝"""
        for bad in ["a<b", "a>b", "a'b", 'a"b', "a;b"]:
            with pytest.raises(ValidationError):
                TagResolveRequest(name=bad)

    def test_too_long_rejected(self):
        """超过 80 字应拒绝"""
        with pytest.raises(ValidationError):
            TagResolveRequest(name="标" * 81)

    def test_80_chars_allowed(self):
        """恰好 80 字合法"""
        req = TagResolveRequest(name="标" * 80)
        assert len(req.name) == 80


# ============================================================================
# TagResolveResponse — 信封与数据
# ============================================================================

class TestTagResolveResponse:
    def test_default_envelope(self):
        """code/message 默认 200/success"""
        resp = TagResolveResponse(
            data=TagResolveData(id=uuid.uuid4(), name="微创", created=False),
            timestamp=datetime.now(),
        )
        assert resp.code == 200
        assert resp.message == "success"
        assert resp.data.created is False

    def test_created_flag_and_source(self):
        """created/source 字段语义"""
        data = TagResolveData(id=uuid.uuid4(), name="自建词", created=True, source="user")
        resp = TagResolveResponse(data=data, timestamp=datetime.now())
        assert resp.data.source == "user"
        assert resp.data.created is True
