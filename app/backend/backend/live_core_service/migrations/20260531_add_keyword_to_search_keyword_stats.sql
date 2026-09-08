-- Migration: 2026-05-31
-- 为 search_keyword_stats 表添加 keyword 字段（原始关键词，保留大小写）
-- 并回填已有数据

-- 1) 添加 keyword 字段
ALTER TABLE search_keyword_stats ADD COLUMN IF NOT EXISTS keyword VARCHAR(255);

-- 2) 回填已有数据：将 keyword_norm 的值复制到 keyword（仅对 keyword 为 NULL 的行）
UPDATE search_keyword_stats SET keyword = keyword_norm WHERE keyword IS NULL;
