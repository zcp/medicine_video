"""政治敏感文本占位客户端测试"""

import os

import pytest

from app.content_safety.political_text.client import (
    PoliticalTextProvider,
    PoliticalTextServiceError,
    check_political_text,
)


class TestPoliticalTextClient:
    @pytest.mark.asyncio
    async def test_placeholder_default_pass(self):
        assert await check_political_text("测试文本", provider=PoliticalTextProvider.PLACEHOLDER) is False

    @pytest.mark.asyncio
    async def test_placeholder_stub_reject(self, monkeypatch):
        monkeypatch.setenv("POLITICAL_TEXT_PLACEHOLDER_REJECT", "true")
        assert await check_political_text("测试", provider=PoliticalTextProvider.PLACEHOLDER) is True

    @pytest.mark.asyncio
    async def test_unconfigured_vendor_raises(self, monkeypatch):
        monkeypatch.delenv("POLITICAL_TEXT_API_KEY", raising=False)
        with pytest.raises(PoliticalTextServiceError):
            await check_political_text("测试", provider=PoliticalTextProvider.ALIYUN)
