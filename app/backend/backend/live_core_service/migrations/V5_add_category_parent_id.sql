-- 融合方案 V5：categories 加分层结构（parent_id + 部分唯一索引）
-- 背景：支持子分类（如 心内科→冠脉介入组）
-- 前置条件：categories 表已存在，V4 已执行
-- 执行顺序：Step A2（第二步，依赖 V4）
-- 关键约束：必须先 DROP 旧 UNIQUE 约束，再创建部分索引——顺序不可逆

-- 1) 删除旧全局唯一约束（幂等 IF EXISTS）
ALTER TABLE categories DROP CONSTRAINT IF EXISTS categories_name_key;

-- 2) 添加 parent_id 自引用外键
ALTER TABLE categories ADD COLUMN IF NOT EXISTS parent_id UUID
    REFERENCES categories(id) ON DELETE RESTRICT;

COMMENT ON COLUMN categories.parent_id IS '父分类ID。NULL=根分类；非NULL=子分类（具体专业方向）';
COMMENT ON COLUMN categories.name IS '分类名称';

-- 3) 创建普通索引
CREATE INDEX IF NOT EXISTS idx_categories_parent_id ON categories(parent_id);

-- 4) 创建部分唯一索引（不支持 IF NOT EXISTS，使用 PL/pgSQL 包裹确保幂等）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE indexname = 'uq_root_category_name'
    ) THEN
        CREATE UNIQUE INDEX uq_root_category_name
        ON categories (name)
        WHERE parent_id IS NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE indexname = 'uq_sub_category_name'
    ) THEN
        CREATE UNIQUE INDEX uq_sub_category_name
        ON categories (parent_id, name)
        WHERE parent_id IS NOT NULL;
    END IF;
END $$;
