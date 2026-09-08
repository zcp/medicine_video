"""Call users service internal batch API for display fields (nickname/avatar)"""

import logging
from typing import Dict, List, Optional
from uuid import UUID

import httpx

logger = logging.getLogger(__name__)


async def fetch_user_profiles(
    user_ids: List[UUID],
) -> Dict[str, Dict[str, Optional[str]]]:
    if not user_ids:
        return {}
    from app.core.config import settings

    base = getattr(settings, "USER_SERVICE_URL", None) or ""
    token = getattr(settings, "INTERNAL_SERVICE_TOKEN", None) or ""
    if not base or not token:
        logger.warning("Skip user profile fetch: USER_SERVICE_URL or INTERNAL_SERVICE_TOKEN not configured")
        return {}

    url = f"{base.rstrip('/')}/api/v1/internal/users/batch"
    unique_ids = list(dict.fromkeys(user_ids))
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                url,
                json={"public_ids": [str(uid) for uid in unique_ids]},
                headers={"X-Internal-Token": token},
            )
        if resp.status_code >= 300:
            logger.warning("User profile fetch fail: status=%s, body=%s", resp.status_code, resp.text[:200])
            return {}
        payload = resp.json() or {}
        items = (payload.get("data") or {}).get("items") or []
        result: Dict[str, Dict[str, Optional[str]]] = {}
        for item in items:
            pid = item.get("public_id")
            if not pid:
                continue
            result[str(pid)] = {
                "username": item.get("username"),
                "nickname": item.get("nickname"),
                "avatar_url": item.get("avatar_url"),
            }
        return result
    except Exception as e:
        logger.warning("User profile fetch exception: %s", e)
        return {}
