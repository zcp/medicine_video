-- ==========================================================
-- 迁移脚本：categories 表新增 parent_id 层级字段
-- 文件：live_core_service/migrations/20260609_add_parent_id_to_categories.sql
-- 执行方式：
--   docker exec live-streaming-saas-v2-main-live_core_service-1 \
--     psql -U postgres -d live_core \
--     -f /app/migrations/20260609_add_parent_id_to_categories.sql
-- ==========================================================

-- 步骤1：新增 parent_id 字段（nullable，现有记录默认 NULL）
ALTER TABLE categories
    ADD COLUMN IF NOT EXISTS parent_id UUID NULL;

-- 步骤2：新增外键约束（自引用，SET NULL 保护）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_categories_parent'
    ) THEN
        ALTER TABLE categories
            ADD CONSTRAINT fk_categories_parent
            FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL;
    END IF;
END $$;

-- 步骤3：新增索引
CREATE INDEX IF NOT EXISTS idx_categories_parent_id
    ON categories(parent_id);

CREATE INDEX IF NOT EXISTS idx_categories_parent_sort
    ON categories(parent_id, sort_order);

-- 步骤4：字段注释
COMMENT ON COLUMN categories.parent_id
    IS '父分类ID（NULL=一级分类，非NULL=二级分类指向其父级）';

-- 验证
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'categories' AND column_name = 'parent_id';
