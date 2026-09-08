-- 分类优化 V8：清理 expert_departments 表中的非标准科室种子数据
-- 背景：V4 迁移插入的部分种子数据存在命名不规范问题（审查报告问题 6）
-- 前置条件：categories 表中 21 条根分类全部存在（Sprint 1 + Sprint 2 已完成）
-- 幂等性：所有 UPDATE/DELETE 使用 EXISTS 守卫

-- 1) 移除「外科门诊」——这是服务类型，不是医学科室名
DELETE FROM expert_departments
WHERE name = '外科门诊'
  AND EXISTS (SELECT 1 FROM expert_departments WHERE name = '外科门诊');

-- 2) 移除「肝外科/超声医学科/介入超声专科」——三个科室拼在一起的复合名
DELETE FROM expert_departments
WHERE name = '肝外科/超声医学科/介入超声专科'
  AND EXISTS (SELECT 1 FROM expert_departments WHERE name = '肝外科/超声医学科/介入超声专科');

-- 3) 拆分「口内修复科」→「口腔内科」+「口腔修复科」
-- 3a. 先重命名现有的「口内修复科」→「口腔内科」
--     口腔内科是口腔科的亚专业，与「口内修复科」语义最接近
UPDATE expert_departments
SET name = '口腔内科',
    synonyms = synonyms || '["口内修复科"]'::jsonb
WHERE name = '口内修复科'
  AND EXISTS (SELECT 1 FROM expert_departments WHERE name = '口内修复科');

-- 3b. 再创建「口腔修复科」（如果尚不存在）
--     先获取口腔科的 category_id，然后插入新记录
DO $$
DECLARE
    cat_id UUID;
BEGIN
    SELECT id INTO cat_id FROM categories WHERE name = '口腔科' AND is_active = true LIMIT 1;
    IF cat_id IS NOT NULL THEN
        INSERT INTO expert_departments (id, name, category_id, synonyms, is_verified)
        SELECT gen_random_uuid(), '口腔修复科', cat_id, '["口腔修复"]'::jsonb, true
        WHERE NOT EXISTS (SELECT 1 FROM expert_departments WHERE name = '口腔修复科');
        RAISE NOTICE '口腔修复科: 已插入或已存在';
    ELSE
        RAISE WARNING '分类"口腔科"不存在，无法插入口腔修复科种子数据——请先执行 Sprint 2';
    END IF;
END $$;

-- 4) 清理「显微创伤外手科」→ 添加标准同义词（不改 name，保持现有记录）
UPDATE expert_departments
SET synonyms = synonyms || '["手外科", "创伤骨科"]'::jsonb
WHERE name = '显微创伤外手科'
  AND NOT (synonyms @> '["手外科"]'::jsonb)
  AND EXISTS (SELECT 1 FROM expert_departments WHERE name = '显微创伤外手科');
