# 直播间与公众号关联 - API URL 一致性检查报告

**版本**: V1.0  
**检查日期**: 2026-02  
**设计文档**: docs/03_系统设计/直播核心功能设计文档_v6_直播间与公众号关联CSM维度设计文档.md

---

## 1. 设计文档中的 API 列表（§4、§10）

| 方法 | 设计文档 URL |
|------|---------------|
| GET | /api/v1/admin/official_accounts |
| GET | /api/v1/admin/official_accounts/{account_id} |
| POST | /api/v1/admin/official_accounts |
| PATCH | /api/v1/admin/official_accounts/{account_id} |
| DELETE | /api/v1/admin/official_accounts/{account_id} |
| GET | /api/v1/rooms/{room_id}/official_accounts |
| POST | /api/v1/admin/rooms/{room_id}/official_accounts |
| DELETE | /api/v1/admin/rooms/{room_id}/official_accounts/{account_id} |
| GET | /api/v1/official_accounts/{account_id}/rooms |

---

## 2. 代码中的路由注册（api/v1/api.py）

- `prefix="/api/v1"` 在 main 中统一添加（settings.API_V1_STR）。
- admin_official_accounts_router：prefix `/admin` → 路径 `/official_accounts`、`/official_accounts/{account_id}` → **完整 URL** `/api/v1/admin/official_accounts`、`/api/v1/admin/official_accounts/{account_id}` ✅
- rooms_official_accounts_router：prefix `/rooms` → 路径 `/{room_id}/official_accounts` → **完整 URL** `/api/v1/rooms/{room_id}/official_accounts` ✅
- admin_rooms_official_accounts_router：prefix `/admin/rooms` → 路径 `/{room_id}/official_accounts`、`/{room_id}/official_accounts/{account_id}` → **完整 URL** `/api/v1/admin/rooms/{room_id}/official_accounts`、`/api/v1/admin/rooms/{room_id}/official_accounts/{account_id}` ✅
- official_accounts_rooms_router：prefix `/official_accounts` → 路径 `/{account_id}/rooms` → **完整 URL** `/api/v1/official_accounts/{account_id}/rooms` ✅

---

## 3. 结论

**一致**: 代码中注册的 9 个端点与设计文档中的 URL 一一对应，无遗漏、无多余，路径与设计文档 §4、§10 一致。
