-- ===========================================================================
-- V11：直播间主分类基线修复 — 为每个直播间设置一个主分类
-- ===========================================================================
-- 背景：live_room_categories.is_primary 字段已存在但从未设置
--       当前所有直播间的 is_primary 均为 false
-- 前置条件：live_room_categories 表已存在
-- 幂等性：NOT EXISTS 守卫——已有主分类的房间不会被覆盖
-- ===========================================================================

UPDATE live_room_categories lrc1
SET is_primary = true
WHERE lrc1.created_at = (
    SELECT MIN(lrc2.created_at)
    FROM live_room_categories lrc2
    WHERE lrc2.room_id = lrc1.room_id
    LIMIT 1
)
AND NOT EXISTS (
    SELECT 1 FROM live_room_categories lrc3
    WHERE lrc3.room_id = lrc1.room_id AND lrc3.is_primary = true
);

-- 验证
SELECT
    lr.title,
    COUNT(lrc.category_id) AS total_cats,
    bool_or(lrc.is_primary) AS has_primary
FROM live_rooms lr
LEFT JOIN live_room_categories lrc ON lr.id = lrc.room_id
GROUP BY lr.id;
-- 预期：所有有分类的房间 has_primary = true
