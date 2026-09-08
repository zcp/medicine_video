"""规则缓存：短 TTL + 管理端更新后立即失效"""

import time
from typing import Any, Dict, List, Optional, Tuple

_cache: Dict[str, Tuple[float, List[Any]]] = {}
DEFAULT_TTL_SECONDS = 60


def get_cached_rules(cache_key: str) -> Optional[List[Any]]:
    entry = _cache.get(cache_key)
    if not entry:
        return None
    expires_at, rules = entry
    if time.time() >= expires_at:
        _cache.pop(cache_key, None)
        return None
    return rules


def set_cached_rules(cache_key: str, rules: List[Any], ttl: int = DEFAULT_TTL_SECONDS) -> None:
    _cache[cache_key] = (time.time() + ttl, rules)


def invalidate_all_rules_cache() -> None:
    _cache.clear()
