"""
手机号工具模块单元测试 - test_phone.py
覆盖 core/phone.py 的归一化与校验函数（阶段 A 出口审查验收项）
"""
import pytest

from app.core.phone import is_valid_cn_phone, normalize_cn_phone, validate_cn_phone


class TestNormalizeCnPhone:
    """测试 normalize_cn_phone 归一化"""

    def test_normalize_pure_11_digits(self):
        """纯 11 位原样返回"""
        assert normalize_cn_phone("13800138000") == "13800138000"

    def test_normalize_spaces(self):
        """空格分隔格式归一化"""
        assert normalize_cn_phone("138 0013 8000") == "13800138000"

    def test_normalize_dashes(self):
        """横线分隔格式归一化"""
        assert normalize_cn_phone("138-0013-8000") == "13800138000"

    def test_normalize_plus86_with_space(self):
        """+86 前缀（含空格）归一化"""
        assert normalize_cn_phone("+86 13800138000") == "13800138000"

    def test_normalize_plus86_no_space(self):
        """+86 前缀（无空格）归一化"""
        assert normalize_cn_phone("+8613800138000") == "13800138000"

    def test_normalize_86_prefix_13_digits(self):
        """86 前缀 13 位归一化"""
        assert normalize_cn_phone("8613800138000") == "13800138000"

    def test_normalize_86_prefix_with_dashes(self):
        """86 前缀 + 横线归一化"""
        assert normalize_cn_phone("86-13800138000") == "13800138000"

    def test_normalize_11_digits_starting_with_86_not_mangled(self):
        """以 86 开头的合法 11 位号不被误删前缀（86123456789 为合法号段）"""
        assert normalize_cn_phone("86123456789") == "86123456789"

    def test_normalize_empty_string(self):
        """空串归一化为空串"""
        assert normalize_cn_phone("") == ""

    def test_normalize_none(self):
        """None 归一化为空串"""
        assert normalize_cn_phone(None) == ""


class TestIsValidCnPhone:
    """测试 is_valid_cn_phone 合法性判断"""

    def test_valid_phone_true(self):
        """合法手机号返回 True"""
        assert is_valid_cn_phone("13800138000") is True

    def test_valid_phone_with_plus86_true(self):
        """带 +86 前缀的合法手机号返回 True"""
        assert is_valid_cn_phone("+8613800138000") is True

    def test_too_short_false(self):
        """过短（10 位）返回 False"""
        assert is_valid_cn_phone("1380013800") is False

    def test_too_long_false(self):
        """过长（12 位）返回 False"""
        assert is_valid_cn_phone("128001380000") is False

    def test_invalid_segment_false(self):
        """非 13-9 号段返回 False"""
        assert is_valid_cn_phone("123456") is False

    def test_with_letters_false(self):
        """含字母返回 False"""
        assert is_valid_cn_phone("1380013800a") is False

    def test_empty_string_false(self):
        """空串返回 False"""
        assert is_valid_cn_phone("") is False

    def test_none_false(self):
        """None 返回 False"""
        assert is_valid_cn_phone(None) is False


class TestValidateCnPhone:
    """测试 validate_cn_phone 校验并返回归一化值"""

    def test_validate_valid_returns_normalized(self):
        """合法输入返回归一化后的纯 11 位"""
        assert validate_cn_phone("+86 138-0013-8000") == "13800138000"

    def test_validate_invalid_raises_value_error(self):
        """非法输入抛 ValueError"""
        with pytest.raises(ValueError):
            validate_cn_phone("12345")

    def test_validate_none_raises_value_error(self):
        """None 抛 ValueError"""
        with pytest.raises(ValueError):
            validate_cn_phone(None)

    def test_validate_empty_raises_value_error(self):
        """空串抛 ValueError"""
        with pytest.raises(ValueError):
            validate_cn_phone("")

    def test_validate_error_message(self):
        """异常消息为固定提示文案"""
        with pytest.raises(ValueError, match="手机号格式不正确"):
            validate_cn_phone("not-a-phone")
