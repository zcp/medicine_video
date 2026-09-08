"""
LiveCore Service - Playback URL Utilities

统一维护 playback_url 的规范化与哈希计算逻辑，供 V6 去重幂等相关代码复用。
"""

from hashlib import sha256


def normalize_playback_url(url: str) -> str:
    """
    对 playback_url 做最小规范化处理。

    当前仅进行 strip() 去除首尾空白，未来如需剔除 tracking 参数，可在此扩展。
    """
    return url.strip() if url is not None else url


def calc_playback_url_hash(url: str) -> str:
    """
    统一的 playback_url 哈希计算函数。
    内部会先调用 normalize_playback_url，避免调用方忘记先规范化。
    """
    normalized = normalize_playback_url(url)
    if normalized is None:
        return None
    return sha256(normalized.encode("utf-8")).hexdigest()


