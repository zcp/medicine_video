-- 融合方案 V7：删除 experts.department 自由文本列 + category_id SET NOT NULL
-- 背景：department 已迁移到 expert_departments 受控词表（V6 完成）
-- 前置条件：V6 迁移脚本已执行且所有专家的 category_id 非 NULL
-- 执行顺序：Step 4（最后一步，不可逆）
-- 幂等性：DROP COLUMN IF EXISTS + ALTER COLUMN SET NOT NULL

-- 0) 前置验证（如有多行 NULL category_id，RAISE EXCEPTION 阻止 DROP）
DO $$
DECLARE
    null_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO null_count FROM experts WHERE category_id IS NULL;
    IF null_count > 0 THEN
        RAISE EXCEPTION '仍有 % 个专家的 category_id 为 NULL，不能删除 department 列。请重新执行 V6 迁移', null_count;
    END IF;
END $$;

-- 1) 删除 department 列（不可逆）
ALTER TABLE experts DROP COLUMN IF EXISTS department;

COMMENT ON COLUMN experts.category_id IS '专家主专业分类，关联全局 categories.id。强制 NOT NULL，兜底指向"其他"分类';

-- 2) category_id 强制 NOT NULL（幂等，已设置则跳过）
ALTER TABLE experts ALTER COLUMN category_id SET NOT NULL;
