-- 私密测播双通道：正式间关联测播间（文档 18）
-- 幂等：可对已有库重复执行；仅 ADD COLUMN / CREATE INDEX，不删数据
--
-- Docker 示例（保留 volume，勿 down -v）:
--   docker compose exec -T postgres psql -U <user> -d live_core < \
--     backend/live_core_service/migrations/20260808_add_live_rooms_source_room_id.sql
-- 或以容器内路径挂载后执行。

ALTER TABLE live_rooms
ADD COLUMN IF NOT EXISTS source_room_id UUID NULL
REFERENCES live_rooms(id) ON DELETE SET NULL;

COMMENT ON COLUMN live_rooms.source_room_id IS
'测播间关联的正式间 ID；仅测播间使用，正式间为 NULL';

-- 一正式间至多一测播间
CREATE UNIQUE INDEX IF NOT EXISTS uq_live_rooms_source_room_id
ON live_rooms (source_room_id)
WHERE source_room_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_live_rooms_source_room_id
ON live_rooms (source_room_id)
WHERE source_room_id IS NOT NULL;
