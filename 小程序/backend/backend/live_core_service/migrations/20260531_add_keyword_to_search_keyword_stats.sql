-- Migration: 添加 keyword 字段到 search_keyword_stats 表
-- 日期: 2026-05-31
-- 说明: 用于存储原始关键词（保留大小写），支持搜索推荐功能

-- 添加 keyword 字段
ALTER TABLE search_keyword_stats ADD COLUMN IF NOT EXISTS keyword VARCHAR(255);

-- 从 keyword_norm 回填现有记录的 keyword 字段（可选）
-- keyword_norm 是小写版本，这里设为 NULL 表示需要新搜索来填充
-- UPDATE search_keyword_stats SET keyword = keyword_norm WHERE keyword IS NULL;
