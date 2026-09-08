-- ============================================================
-- V14_add_category_standard.sql
-- categories 表新增 standard 列（标准/扩展科目标记，阶段6B）
--
-- 背景（分类系统治理方案 §5 阶段6B）：
--   - standard=true：name 必须命中名录标准名清单（category_constants 维护）
--   - standard=false：扩展科目（如"生殖医学科"、"其他"兜底），name 放行合规名
--   - 存量回填：'其他' / '生殖医学科' 标 false，其余默认 true
--
-- 幂等性：
--   - ADD COLUMN IF NOT EXISTS 可重复执行
--   - UPDATE 按 name 精确匹配（幂等）
--
-- 适用库：live_core_service
-- ============================================================

ALTER TABLE categories
    ADD COLUMN IF NOT EXISTS standard BOOLEAN NOT NULL DEFAULT TRUE;

-- 扩展科目回填（'其他' 兜底 + '生殖医学科' 非名录一级）
UPDATE categories
SET standard = FALSE
WHERE name IN ('其他', '生殖医学科');
