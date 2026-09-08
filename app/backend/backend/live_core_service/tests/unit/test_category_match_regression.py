"""
分类系统核心回归测试（K6，阶段 1B）

覆盖：
  1. _match_broad_category 匹配算法 12+ 用例（别名表/子串/兜底）
  2. is_test_category_name 测试前缀识别（K3/K5 共用）
  3. category_constants 单一真相源派生一致性

运行方式:
  pytest tests/unit/test_category_match_regression.py -v
"""
import pytest

from app.core.category_constants import (
    CATEGORIES_SEED_DATA,
    ROOT_CATEGORIES,
    CATEGORY_PARENT_MAP,
    ALL_CATEGORY_NAMES_SORTED,
    STANDARD_CATEGORY_NAMES,
    DEPARTMENT_CATEGORY_MAP,
    is_test_category_name,
)
from app.services.expert_service import _match_broad_category


# ============================================================
# 1. _match_broad_category 匹配算法回归（12 用例，P0-3 语义：返回二级名）
# ============================================================

MATCH_CASES = [
    # (输入科室文本, 期望 (规范化文本, 匹配分类名) 或 None)
    ("心内科-冠脉组", ("心内科-冠脉组", "心内科")),
    ("骨科-脊柱组", ("骨科-脊柱组", "骨科")),
    ("消化科门诊", ("消化科门诊", "消化科")),
    ("乳腺外科", ("乳腺外科", "普通外科")),          # 别名表
    ("骨肿瘤科", ("骨肿瘤科", "骨科")),              # 别名表（P0-3 修复点）
    ("妇产科-产科", ("妇产科-产科", "妇产科")),
    ("眼科门诊", ("眼科门诊", "眼科")),
    ("变态反应专科", ("变态反应专科", "变态反应科")),  # K2 修正后（原为"其他"）
    ("外科门诊", ("外科门诊", "其他")),              # V8 已删数据，别名保留
    ("内分泌科-糖尿病组", ("内分泌科-糖尿病组", "内分泌科")),
    ("肿瘤科-化疗组", ("肿瘤科-化疗组", "肿瘤科")),
    ("男科", ("男科", "泌尿外科")),                  # K2 新增（原无条目）
    ("结构性心脏病组", None),                        # 无法匹配 → 兜底
    ("", None),
    (None, None),
]


@pytest.mark.parametrize("dept_text,expected", MATCH_CASES)
def test_match_broad_category(dept_text, expected):
    """匹配算法回归：别名表优先 + 二级优先子串 + 兜底 None"""
    result = _match_broad_category(dept_text)
    if expected is None:
        assert result is None, f"输入 {dept_text!r} 期望 None，实际 {result}"
    else:
        assert result == expected, f"输入 {dept_text!r} 期望 {expected}，实际 {result}"


def test_match_secondary_priority_over_root():
    """二级优先：'内科' 与 '心内科' 同时是子串时，应匹配更具体的二级名"""
    result = _match_broad_category("心内科门诊")
    assert result is not None
    assert result[1] == "心内科"


# ============================================================
# 2. is_test_category_name 测试前缀识别（K3/K5 共用）
# ============================================================

TEST_NAME_CASES = [
    ("分类_abc123", True),
    ("分类1_abc", True),
    ("test_cat_x", True),
    ("TEST_CAT", True),
    ("科室_abc", True),
    ("源_abc", True),
    ("一级_abc", True),
    ("目标_abc", True),
    ("二级A_abc", True),
    ("子_abc", True),
    ("父_abc", True),
    ("根_abc", True),
    ("活跃_abc", True),
    ("空分类_abc", True),
    ("重复分类_abc", True),
    ("新分类_abc", True),
    ("唯一名_abc", True),
    ("神经内科_abc", True),
    ("停用_abc", True),
    ("禁用_abc", True),
    ("D_abc", True),
    ("测试分类", True),
    ("普通外科", False),
    ("心内科", False),
    ("内科", False),
    ("其他", False),
    ("", False),
    (None, False),
]


@pytest.mark.parametrize("name,expected", TEST_NAME_CASES)
def test_is_test_category_name(name, expected):
    """测试前缀识别：模式命中返回 True，标准名/空值返回 False"""
    assert is_test_category_name(name) is expected


# ============================================================
# 3. category_constants 单一真相源派生一致性
# ============================================================

def test_constants_derivation_consistency():
    """常量派生一致性：35 条 = 16 一级 + 19 二级；派生集合与种子一致"""
    assert len(CATEGORIES_SEED_DATA) == 35
    assert len(ROOT_CATEGORIES) == 16
    assert len(CATEGORY_PARENT_MAP) == 19
    assert len(ALL_CATEGORY_NAMES_SORTED) == 35
    assert len(STANDARD_CATEGORY_NAMES) == 29
    # 二级在前（防止子串误匹配）
    assert ALL_CATEGORY_NAMES_SORTED.index("心内科") < ALL_CATEGORY_NAMES_SORTED.index("内科")


def test_standard_false_categories():
    """standard=false 的 6 条业务扩展分类"""
    std_false = sorted(c["name"] for c in CATEGORIES_SEED_DATA if not c["standard"])
    assert std_false == sorted(["生殖医学科", "其他", "心胸外科", "血管外科", "器官移植科", "烧伤与创面修复科"])


def test_department_category_map_values_are_real_categories():
    """别名表所有值必须命中常量分类名（防映射指向不存在的分类）"""
    all_names = {c["name"] for c in CATEGORIES_SEED_DATA}
    for alias, target in DEPARTMENT_CATEGORY_MAP.items():
        assert target in all_names, f"别名 {alias!r} 指向不存在的分类 {target!r}"
