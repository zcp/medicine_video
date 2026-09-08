"""
Smoke test for LiveCore backend deployment.

Run inside the live_core_service container:
    docker exec live_core_service-1 python /app/scripts/smoke_test.py

Exit code: 0 = all passed, 1 = any failed
"""

import asyncio
import sys
import traceback
from typing import List, Tuple


# ============================================================
# Test result tracking
# ============================================================
results: List[Tuple[str, bool, str]] = []


def test(name: str, passed: bool, detail: str = "") -> None:
    results.append((name, passed, detail))
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {name}")
    if detail:
        print(f"         {detail}")


async def test_content_safety_block() -> bool:
    try:
        from app.database import AsyncSessionLocal
        from app.content_safety.service import check_scene_fields

        async with AsyncSessionLocal() as db:
            r = await check_scene_fields(
                db, "message",
                {"content": "加微信 联系我"},
                resource_type="message",
            )
            return r.decision == "block"
    except Exception as e:
        if "ContentSafetyBlockedException" in str(type(e)):
            return True  # exception also means blocked
        return False


async def test_content_safety_allow() -> bool:
    try:
        from app.database import AsyncSessionLocal
        from app.content_safety.service import check_scene_fields

        async with AsyncSessionLocal() as db:
            r = await check_scene_fields(
                db, "message",
                {"content": "正常医学讨论内容"},
                resource_type="message",
            )
            return r.passed and r.decision == "allow"
    except Exception:
        return False


async def test_rate_limiting() -> bool:
    try:
        from uuid import uuid4
        from app.core.redis_cache import check_message_rate_limit

        uid = uuid4()
        rid = uuid4()
        first = await check_message_rate_limit(uid, rid)
        second = await check_message_rate_limit(uid, rid)
        return first is True and second is False
    except Exception:
        return False


async def test_cache_invalidation() -> bool:
    try:
        from uuid import uuid4
        from app.core.redis_cache import get_redis

        client = await get_redis()
        if client is None:
            return False
        # Write a test cache entry
        test_key = f"smoke_test:{uuid4()}"
        await client.set(test_key, "1", ex=10)
        exists = await client.exists(test_key)
        if not exists:
            return False
        await client.delete(test_key)
        gone = await client.exists(test_key) == 0
        return gone
    except Exception:
        return False


async def check_url(method: str, url: str, expected_status: int) -> bool:
    """Verify an HTTP endpoint returns the expected status code."""
    try:
        from httpx import AsyncClient

        async with AsyncClient(base_url="http://localhost:8000") as c:
            resp = await c.request(method, url)
            return resp.status_code == expected_status
    except Exception:
        return False


async def main() -> int:
    print("=" * 60)
    print("LiveCore Smoke Test")
    print("=" * 60)

    # ---- Code-level tests (no network dependency) ----
    print("\n--- Content Safety ---")
    test("block banned content", await test_content_safety_block(),
         "check_scene_fields('加微信 联系我') should be blocked")
    test("allow normal content", await test_content_safety_allow(),
         "check_scene_fields('正常医学讨论内容') should be allowed")

    print("\n--- Rate Limiting ---")
    test("first call allowed, second rejected",
         await test_rate_limiting(),
         "check_message_rate_limit with fresh user+room")

    print("\n--- Cache ---")
    test("set/get/delete round trip",
         await test_cache_invalidation(),
         "Redis basic operations")

    # ---- HTTP endpoint tests ----
    print("\n--- Admin Endpoints (401 without token) ---")
    endpoints = [
        ("GET", "/api/v1/admin/rooms", "admin rooms list"),
        ("GET", "/api/v1/admin/stats/daily", "admin stats daily"),
        ("GET", "/api/v1/admin/sessions/today", "admin sessions today"),
        ("GET", "/api/v1/admin/content-safety/rules", "content safety rules"),
        ("GET", "/api/v1/admin/content-safety/logs", "content safety logs"),
        ("GET", "/api/v1/admin/messages", "admin messages list"),
        ("POST", "/api/v1/internal/users/00000000-0000-0000-0000-000000000000/deactivate-cleanup",
         "internal cleanup (503 if no token, else 403)"),
    ]
    public_endpoints = [
        ("GET", "/api/v1/health", "health check"),
        ("GET", "/api/v1/search?q=test", "search"),
        ("GET", "/api/v1/experts?page=1&size=5", "experts list"),
    ]

    for method, path, label in endpoints:
        expected = 401 if "internal" not in path else None
        expected = 401 if "internal" not in path else (401, 503)
        if "internal" in path:
            expected = 503  # INTERNAL_SERVICE_TOKEN not configured
        else:
            expected = 401
        ok = await check_url(method, path, expected)
        test(f"{label} -> {expected}", ok, f"{method} {path}")

    print("\n--- Public Endpoints (200) ---")
    for method, path, label in public_endpoints:
        ok = await check_url(method, path, 200)
        test(f"{label}", ok, f"{method} {path}")

    # ---- Summary ----
    passed = sum(1 for _, p, _ in results if p)
    failed = len(results) - passed
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{len(results)} passed, {failed} failed")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
