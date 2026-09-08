-- live_rooms.category_id 遗留字段清理迁移
-- 
-- 背景：category_id 曾是 live_rooms 表的直接外键字段，
-- 现已迁移至 live_room_categories 多对多关联表。
-- ORM 模型 (app/models/live_core.py) 中已移除该字段，
-- 响应 Schema 中已移除，API 中间件拒绝包含该字段的请求。
-- 本迁移从数据库中彻底移除该遗留列。
--
-- 执行前请确认 live_room_categories 表中数据已完整覆盖。

ALTER TABLE live_rooms
DROP COLUMN IF EXISTS category_id;

COMMENT ON TABLE live_rooms IS '直播房间表（已移除 category_id 遗留列，请使用 live_room_categories 表）';
