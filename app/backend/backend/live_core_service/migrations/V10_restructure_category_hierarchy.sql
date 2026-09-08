-- ===========================================================================
-- 分类系统国家医学标准重构：V10 建立一级/二级层级关系
-- ===========================================================================
-- 背景：将 25 个平铺根分类重构为符合卫生部《医疗机构诊疗科目名录》的层级结构
--        新增"内科""外科"为一级科目，将 16 条原根分类设为对应的二级科目
-- 前置条件：categories 表中已存在 25 个分类（seed.py 已执行）
-- 依赖：V5_add_category_parent_id.sql（parent_id 列已创建）
-- 执行顺序：Phase A（第三步，依赖 V4 + V5，先于 Phase B 代码部署）
-- 幂等性：INSERT 用 WHERE NOT EXISTS，UPDATE 只改 parent_id IS NULL 的记录
-- 回滚方案：见文件尾部
-- ===========================================================================

-- 1) 新增"内科""外科"一级科目（幂等）
-- 注意：sort_order 由 SQL 动态计算（取当前最小 sort_order - 1），与 seed.py
-- CATEGORIES_SEED_DATA 中静态定义的 sort_order（内科=1, 外科=2）不一致。
-- 此差异不影响功能——sort_order 仅用于列表排序。全新部署时统一执行 seed.py。
INSERT INTO categories (id, name, slug, sort_order, parent_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), '内科', 'internal-medicine',
       (SELECT COALESCE(MIN(sort_order), 1) - 1 FROM categories WHERE parent_id IS NULL),
       NULL, true, now(), now()
WHERE NOT EXISTS (SELECT 1 FROM categories WHERE name = '内科' AND parent_id IS NULL);

INSERT INTO categories (id, name, slug, sort_order, parent_id, is_active, created_at, updated_at)
SELECT gen_random_uuid(), '外科', 'surgery',
       (SELECT COALESCE(MIN(sort_order), 1) - 1 FROM categories WHERE parent_id IS NULL),
       NULL, true, now(), now()
WHERE NOT EXISTS (SELECT 1 FROM categories WHERE name = '外科' AND parent_id IS NULL);

-- 2) 将 7 个内科子类挂到"内科"下（只改 parent_id 仍为 NULL 的记录——幂等）
DO $$
DECLARE
    internal_id UUID;
BEGIN
    SELECT id INTO internal_id FROM categories
    WHERE name = '内科' AND parent_id IS NULL AND is_active = true LIMIT 1;
    IF internal_id IS NOT NULL THEN
        UPDATE categories SET parent_id = internal_id
        WHERE name IN ('心内科','消化科','内分泌科','呼吸内科','肾内科','血液科','风湿免疫科')
          AND parent_id IS NULL;
        RAISE NOTICE '内科子类已挂载到内科(id=%)', internal_id;
    ELSE
        RAISE WARNING '分类"内科"不存在，跳过内科子类挂载';
    END IF;
END $$;

-- 3) 将 9 个外科子类挂到"外科"下（同上）
DO $$
DECLARE
    surgery_id UUID;
BEGIN
    SELECT id INTO surgery_id FROM categories
    WHERE name = '外科' AND parent_id IS NULL AND is_active = true LIMIT 1;
    IF surgery_id IS NOT NULL THEN
        UPDATE categories SET parent_id = surgery_id
        WHERE name IN ('普通外科','神经外科','骨科','泌尿外科','心胸外科','血管外科','整形外科','器官移植科','烧伤与创面修复科')
          AND parent_id IS NULL;
        RAISE NOTICE '外科子类已挂载到外科(id=%)', surgery_id;
    ELSE
        RAISE WARNING '分类"外科"不存在，跳过外科子类挂载';
    END IF;
END $$;

-- 4) 验证（预期: root_count=11, child_count=16）
SELECT
    COUNT(*) FILTER (WHERE parent_id IS NULL AND is_active = true)  AS root_count,
    COUNT(*) FILTER (WHERE parent_id IS NOT NULL AND is_active = true) AS child_count
FROM categories;


-- ===========================================================================
-- 回滚脚本（紧急使用）
-- ===========================================================================
-- 步骤：
-- 1) 恢复子类的 parent_id=NULL（只改当前挂在内科/外科下的记录）
-- 2) 删除新增的一级科目（必须先执行步骤 1，否则 RESTRICT 阻止删除）

-- 步骤 1：解除子类关联
-- DO $$
-- DECLARE
--     internal_id UUID;
--     surgery_id UUID;
-- BEGIN
--     SELECT id INTO internal_id FROM categories WHERE name = '内科' AND parent_id IS NULL LIMIT 1;
--     SELECT id INTO surgery_id FROM categories WHERE name = '外科' AND parent_id IS NULL LIMIT 1;
--     IF internal_id IS NOT NULL THEN
--         UPDATE categories SET parent_id = NULL WHERE parent_id = internal_id;
--     END IF;
--     IF surgery_id IS NOT NULL THEN
--         UPDATE categories SET parent_id = NULL WHERE parent_id = surgery_id;
--     END IF;
-- END $$;
--
-- -- 步骤 2：删除内科/外科
-- DELETE FROM categories WHERE name IN ('内科', '外科') AND parent_id IS NULL;
-- ===========================================================================
