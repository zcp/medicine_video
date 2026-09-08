"""默认内容安全规则种子（live_core 库 — 医学合规词库）"""

from app.content_safety.medical_lexicon_seed import run_medical_lexicon_seed

__all__ = ["seed_default_rules"]


async def seed_default_rules(db):
    """幂等写入医学合规规则并迁移旧 V2.2 规则"""
    return await run_medical_lexicon_seed(db)
