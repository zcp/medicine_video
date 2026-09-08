-- wechat-v1：创建 expert_departments + experts.department_id/category_id（过渡期双轨）
-- 基于 _port_from_huang/migrations/V4_create_expert_departments.sql
-- 额外：experts.category_id（可空 FK）、expert_departments.source/created_by
-- 禁止：不 DROP experts.department；不 DROP live_rooms.category_id；不改 category_id NOT NULL
-- 幂等：IF NOT EXISTS / ON CONFLICT DO NOTHING

-- 1) 创建 expert_departments 表
CREATE TABLE IF NOT EXISTS expert_departments (
    id UUID PRIMARY KEY,
    name VARCHAR(120) UNIQUE NOT NULL,
    category_id UUID NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    synonyms JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    source VARCHAR(50),
    created_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE expert_departments IS '专家科室受控词表。将 department 从自由文本变为受控词表';
COMMENT ON COLUMN expert_departments.name IS '标准科室名称，全局唯一。如"乳腺外科"';
COMMENT ON COLUMN expert_departments.category_id IS '科室所属主分类ID。ON DELETE RESTRICT 防止误删分类';
COMMENT ON COLUMN expert_departments.synonyms IS '同义词列表 JSON 数组。导入时用于容错匹配';
COMMENT ON COLUMN expert_departments.is_verified IS '是否已审核。false=自适应创建待确认，true=已审核标准词';
COMMENT ON COLUMN expert_departments.source IS '创建来源：auto_match, csv_import, manual_create, admin_api, seed_v4, unknown_legacy';
COMMENT ON COLUMN expert_departments.created_by IS '创建人 user_id。auto_match 来源时为 NULL';

-- 兼容：表已存在但缺列时补齐
ALTER TABLE expert_departments ADD COLUMN IF NOT EXISTS source VARCHAR(50);
ALTER TABLE expert_departments ADD COLUMN IF NOT EXISTS created_by UUID;

CREATE INDEX IF NOT EXISTS idx_expert_departments_category_id ON expert_departments(category_id);
CREATE INDEX IF NOT EXISTS idx_expert_departments_is_active ON expert_departments(is_active);
CREATE INDEX IF NOT EXISTS idx_expert_departments_is_verified ON expert_departments(is_verified);
CREATE INDEX IF NOT EXISTS idx_expert_departments_source ON expert_departments(source);
CREATE INDEX IF NOT EXISTS idx_expert_departments_created_by ON expert_departments(created_by);

-- 2) experts 表新增 department_id / category_id（均可空，过渡期）
ALTER TABLE experts ADD COLUMN IF NOT EXISTS department_id UUID
    REFERENCES expert_departments(id) ON DELETE SET NULL;

COMMENT ON COLUMN experts.department_id IS '科室ID，关联 expert_departments 受控词表。NULL 表示未映射';

CREATE INDEX IF NOT EXISTS idx_experts_department_id ON experts(department_id);

ALTER TABLE experts ADD COLUMN IF NOT EXISTS category_id UUID
    REFERENCES categories(id) ON DELETE SET NULL;

COMMENT ON COLUMN experts.category_id IS '专家主分类缓存列（由科室词表推导）。过渡期可空；终态再收紧 NOT NULL';

CREATE INDEX IF NOT EXISTS idx_experts_category_id ON experts(category_id);

-- 3) 插入种子科室数据；缺分类名则 WARNING 跳过
DO $$
DECLARE
    cat_id UUID;
BEGIN
    -- 普通外科类（8 条）
    SELECT id INTO cat_id FROM categories WHERE name = '普通外科' AND is_active = true LIMIT 1;
    IF cat_id IS NOT NULL THEN
        INSERT INTO expert_departments (id, name, category_id, is_verified, source) VALUES
            (gen_random_uuid(), '乳腺外科', cat_id, true, 'seed_v4'),
            (gen_random_uuid(), '甲状腺外科', cat_id, true, 'seed_v4'),
            (gen_random_uuid(), '肝胆外科', cat_id, true, 'seed_v4'),
            (gen_random_uuid(), '胃肠外科一科', cat_id, true, 'seed_v4'),
            (gen_random_uuid(), '胃肠外科二科', cat_id, true, 'seed_v4'),
            (gen_random_uuid(), '胃肠外科三科', cat_id, true, 'seed_v4'),
            (gen_random_uuid(), '胆胰外科', cat_id, true, 'seed_v4'),
            (gen_random_uuid(), '肝外科', cat_id, true, 'seed_v4')
        ON CONFLICT (name) DO NOTHING;
        RAISE NOTICE '普通外科类种子数据: 8 条';
    ELSE
        RAISE WARNING '分类"普通外科"不存在，跳过对应种子数据';
    END IF;

    -- 骨科类（5 条）
    SELECT id INTO cat_id FROM categories WHERE name = '骨科' AND is_active = true LIMIT 1;
    IF cat_id IS NOT NULL THEN
        INSERT INTO expert_departments (id, name, category_id, is_verified, source) VALUES
            (gen_random_uuid(), '脊柱外科', cat_id, true, 'seed_v4'),
            (gen_random_uuid(), '关节外科', cat_id, true, 'seed_v4'),
            (gen_random_uuid(), '骨肿瘤科', cat_id, true, 'seed_v4'),
            (gen_random_uuid(), '运动医学科', cat_id, true, 'seed_v4'),
            (gen_random_uuid(), '显微创伤外手科', cat_id, true, 'seed_v4')
        ON CONFLICT (name) DO NOTHING;
        RAISE NOTICE '骨科类种子数据: 5 条';
    ELSE
        RAISE WARNING '分类"骨科"不存在，跳过对应种子数据';
    END IF;

    -- 妇产科类（2 条）
    SELECT id INTO cat_id FROM categories WHERE name = '妇产科' AND is_active = true LIMIT 1;
    IF cat_id IS NOT NULL THEN
        INSERT INTO expert_departments (id, name, category_id, is_verified, source) VALUES
            (gen_random_uuid(), '妇科', cat_id, true, 'seed_v4'),
            (gen_random_uuid(), '产科', cat_id, true, 'seed_v4')
        ON CONFLICT (name) DO NOTHING;
        RAISE NOTICE '妇产科类种子数据: 2 条';
    ELSE
        RAISE WARNING '分类"妇产科"不存在，跳过对应种子数据';
    END IF;

    -- 耳鼻喉科类（3 条）
    SELECT id INTO cat_id FROM categories WHERE name = '耳鼻喉科' AND is_active = true LIMIT 1;
    IF cat_id IS NOT NULL THEN
        INSERT INTO expert_departments (id, name, category_id, is_verified, source) VALUES
            (gen_random_uuid(), '鼻专科', cat_id, true, 'seed_v4'),
            (gen_random_uuid(), '耳专科', cat_id, true, 'seed_v4'),
            (gen_random_uuid(), '咽喉专科', cat_id, true, 'seed_v4')
        ON CONFLICT (name) DO NOTHING;
        RAISE NOTICE '耳鼻喉科类种子数据: 3 条';
    ELSE
        RAISE WARNING '分类"耳鼻喉科"不存在，跳过对应种子数据';
    END IF;

    -- 器官移植科类（3 条）
    SELECT id INTO cat_id FROM categories WHERE name = '器官移植科' AND is_active = true LIMIT 1;
    IF cat_id IS NOT NULL THEN
        INSERT INTO expert_departments (id, name, category_id, is_verified, source) VALUES
            (gen_random_uuid(), '肾移植专科', cat_id, true, 'seed_v4'),
            (gen_random_uuid(), '器官移植科/肾移植专科', cat_id, true, 'seed_v4'),
            (gen_random_uuid(), '器官移植科/肝移植专科', cat_id, true, 'seed_v4')
        ON CONFLICT (name) DO NOTHING;
        RAISE NOTICE '器官移植科类种子数据: 3 条';
    ELSE
        RAISE WARNING '分类"器官移植科"不存在，跳过对应种子数据';
    END IF;

    -- 泌尿外科类（1 条）
    SELECT id INTO cat_id FROM categories WHERE name = '泌尿外科' AND is_active = true LIMIT 1;
    IF cat_id IS NOT NULL THEN
        INSERT INTO expert_departments (id, name, category_id, is_verified, source) VALUES
            (gen_random_uuid(), '泌尿外科/男科', cat_id, true, 'seed_v4')
        ON CONFLICT (name) DO NOTHING;
        RAISE NOTICE '泌尿外科类种子数据: 1 条';
    ELSE
        RAISE WARNING '分类"泌尿外科"不存在，跳过对应种子数据';
    END IF;

    -- 生殖医学相关：wechat 无「生殖医学科」根分类，尝试挂到「妇产科」；再尝试「生殖医学中心」
    SELECT id INTO cat_id FROM categories WHERE name = '妇产科' AND is_active = true LIMIT 1;
    IF cat_id IS NULL THEN
        SELECT id INTO cat_id FROM categories WHERE name = '生殖医学中心' AND is_active = true LIMIT 1;
    END IF;
    IF cat_id IS NOT NULL THEN
        INSERT INTO expert_departments (id, name, category_id, is_verified, source) VALUES
            (gen_random_uuid(), '生殖医学中心', cat_id, true, 'seed_v4'),
            (gen_random_uuid(), '生殖男科专科', cat_id, true, 'seed_v4'),
            (gen_random_uuid(), '男科/生殖医学中心', cat_id, true, 'seed_v4')
        ON CONFLICT (name) DO NOTHING;
        RAISE NOTICE '生殖医学相关种子数据: 3 条';
    ELSE
        RAISE WARNING '分类"妇产科/生殖医学中心"不存在，跳过对应种子数据';
    END IF;

    -- 心胸外科类（1 条）
    SELECT id INTO cat_id FROM categories WHERE name = '心胸外科' AND is_active = true LIMIT 1;
    IF cat_id IS NOT NULL THEN
        INSERT INTO expert_departments (id, name, category_id, is_verified, source) VALUES
            (gen_random_uuid(), '胸外科', cat_id, true, 'seed_v4')
        ON CONFLICT (name) DO NOTHING;
        RAISE NOTICE '心胸外科类种子数据: 1 条';
    ELSE
        RAISE WARNING '分类"心胸外科"不存在，跳过对应种子数据';
    END IF;

    -- 口腔科类（2 条）
    SELECT id INTO cat_id FROM categories WHERE name = '口腔科' AND is_active = true LIMIT 1;
    IF cat_id IS NOT NULL THEN
        INSERT INTO expert_departments (id, name, category_id, is_verified, source) VALUES
            (gen_random_uuid(), '口内修复科', cat_id, true, 'seed_v4'),
            (gen_random_uuid(), '口腔颌面外科', cat_id, true, 'seed_v4')
        ON CONFLICT (name) DO NOTHING;
        RAISE NOTICE '口腔科类种子数据: 2 条';
    ELSE
        RAISE WARNING '分类"口腔科"不存在，跳过对应种子数据';
    END IF;

    -- 儿科类（1 条）
    SELECT id INTO cat_id FROM categories WHERE name = '儿科' AND is_active = true LIMIT 1;
    IF cat_id IS NOT NULL THEN
        INSERT INTO expert_departments (id, name, category_id, is_verified, source) VALUES
            (gen_random_uuid(), '小儿外科', cat_id, true, 'seed_v4')
        ON CONFLICT (name) DO NOTHING;
        RAISE NOTICE '儿科类种子数据: 1 条';
    ELSE
        RAISE WARNING '分类"儿科"不存在，跳过对应种子数据';
    END IF;

    -- 其他类（3 条）
    SELECT id INTO cat_id FROM categories WHERE name = '其他' AND is_active = true LIMIT 1;
    IF cat_id IS NOT NULL THEN
        INSERT INTO expert_departments (id, name, category_id, is_verified, source) VALUES
            (gen_random_uuid(), '变态反应专科', cat_id, true, 'seed_v4'),
            (gen_random_uuid(), '外科门诊', cat_id, true, 'seed_v4'),
            (gen_random_uuid(), '肝外科/超声医学科/介入超声专科', cat_id, true, 'seed_v4')
        ON CONFLICT (name) DO NOTHING;
        RAISE NOTICE '其他类种子数据: 3 条';
    ELSE
        RAISE WARNING '分类"其他"不存在，跳过对应种子数据';
    END IF;

    RAISE NOTICE '=== 种子科室数据插入完成 ===';
END $$;
