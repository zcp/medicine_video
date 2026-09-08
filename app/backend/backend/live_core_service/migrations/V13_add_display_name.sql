-- ============================================================
-- V13_add_display_name.sql
-- categories 表新增 display_name 列（标准名/口语名分离，阶段6A）
--
-- 背景（分类系统治理方案 §4.3/§5 阶段6A）：
--   - name 存名录标准名（驱动匹配算法），display_name 存口语名（驱动 C 端展示）
--   - 存量回填 display_name = name（老前端无感；新分类由运营按需设置口语名）
--
-- 幂等性：
--   - ADD COLUMN IF NOT EXISTS 可重复执行
--   - 回填仅补 NULL（不覆盖已设置的 display_name）
--
-- 适用库：live_core_service（双库中的内容管理主库）
-- ============================================================

ALTER TABLE categories
    ADD COLUMN IF NOT EXISTS display_name VARCHAR(100);

-- 存量回填：display_name = name（仅 NULL 时）
UPDATE categories
SET display_name = name
WHERE display_name IS NULL;
