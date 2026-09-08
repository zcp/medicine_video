# 直播间与公众号关联模块 - 测试对齐与修复报告

**模块名**: liveroom_official_accounts  
**设计文档**: 直播核心功能设计文档_v6_直播间与公众号关联CSM维度设计文档.md  
**测试模式**: incremental  
**最大迭代次数**: 3  

## 执行结果

- **状态**: 全部通过  
- **CRUD 单元测试**: 12 个通过  
- **Service 单元测试**: 8 个通过  
- **API 集成测试**: 9 个通过  
- **合计**: 30 passed  

## 修复项摘要

### 1. conftest（测试配置）

- **AsyncClient (httpx 0.25+)**: 将 `AsyncClient(app=app, base_url=...)` 改为 `AsyncClient(transport=ASGITransport(app=app), base_url=...)`，两处（`async_client`、`async_client_with_auth`）。
- **official_accounts 表未创建**: 第二个 `setup_database` fixture 覆盖了第一个，仅创建了 UsersBase 与 LiveCoreBase。在第二个 `setup_database` 中增加对 `app.database.Base` 的 `create_all`，并在此前 import `app.models.content_management` 与 `app.models.liveroom_official_accounts`，确保 `official_accounts`、`live_room_official_accounts` 等表在测试库中存在。

### 2. API 与 Service 层 JSON 序列化

- **UUID 不可 JSON 序列化**: 接口返回中使用 `item.model_dump()` 导致 `Object of type UUID is not JSON serializable`。
- **修改**: 在 `app/api/v1/endpoints/liveroom_official_accounts.py` 中，所有 `success_response(data=item.model_dump())` 及列表项改为 `model_dump(mode="json")`；在 `app/services/liveroom_official_accounts_service.py` 中，返回 dict 内的 `data.model_dump()` 及 `accounts` 列表项改为 `model_dump(mode="json")`。

### 3. 集成测试数据可见性

- **404 / 接口看不到测试数据**: 在部分 API 测试中，仅在 `db_session` 中 `add` + `flush`，未 `commit`，请求使用的独立 DB 会话看不到未提交数据。
- **修改**: 在 `test_get_rooms_official_accounts_success`、`test_set_room_official_accounts_admin`、`test_get_official_accounts_rooms_paginated` 中，在发起 HTTP 请求前对创建好的 room/account 等执行 `await db.commit()`。

## 测试文件

- `backend/live_core_service/tests/unit/test_crud_liveroom_official_accounts.py`
- `backend/live_core_service/tests/unit/test_service_liveroom_official_accounts.py`
- `backend/live_core_service/tests/integration/test_api_liveroom_official_accounts.py`

## 运行命令

```bash
cd backend/live_core_service
python -m pytest tests/unit/test_crud_liveroom_official_accounts.py tests/unit/test_service_liveroom_official_accounts.py tests/integration/test_api_liveroom_official_accounts.py -v --tb=line
```
