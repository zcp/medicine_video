#!/usr/bin/env python3
"""
历史手机号数据归一化清洗脚本

扫描 users.phone_number 中的脏格式记录（+86/86 前缀、空格、横线等），
统一清洗为纯 11 位格式（复用 core/phone.py 的归一化规则）。

安全设计：
- 默认 dry-run 预演，仅输出报告不写库；显式 --execute 才实际写入（带确认提示）
- 幂等：已归一化记录自动跳过，可重复执行
- 冲突保护：归一化目标与库中其他用户冲突时跳过并列入"重复账号"清单
- 失败兜底：批量提交遇唯一约束冲突时回滚并逐条重试，失败条目计入冲突清单

运行方式（users/ 根目录）：
  python -m app.scripts.normalize_phone_numbers            # 预演
  python -m app.scripts.normalize_phone_numbers --execute  # 实际执行（请先备份）
"""

import argparse
import logging
import sys
from typing import List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

MASK_HEAD_LEN = 3
MASK_TAIL_LEN = 4


def mask_phone(phone: str) -> str:
    """手机号打码，例如 138****8000；过短则整体掩码。

    Args:
        phone: 原始手机号

    Returns:
        打码后的手机号
    """
    phone = str(phone or "")
    if len(phone) < MASK_HEAD_LEN + MASK_TAIL_LEN:
        return "*" * len(phone) if phone else "(空)"
    return (
        phone[:MASK_HEAD_LEN]
        + "*" * (len(phone) - MASK_HEAD_LEN - MASK_TAIL_LEN)
        + phone[-MASK_TAIL_LEN:]
    )


def classify_phone(phone: str) -> Tuple[str, str]:
    """分类手机号，决定清洗动作。

    Args:
        phone: 原始手机号

    Returns:
        ("already", "") 已归一化，跳过；
        ("invalid", "") 非法值，人工审核；
        ("normal", normalized) 可清洗，返回归一化目标值
    """
    from app.core.phone import validate_cn_phone

    try:
        normalized = validate_cn_phone(phone)
    except ValueError:
        return ("invalid", "")
    if normalized == phone:
        return ("already", "")
    return ("normal", normalized)


def scan_and_normalize(
    session,
    *,
    model=None,
    execute: bool = False,
    batch_size: int = 500,
    limit: int = 0,
):
    """扫描并归一化历史脏格式手机号（主流程，模型可注入以便无库测试）。

    Args:
        session: 数据库会话（autoflush=False）
        model: ORM 模型类（默认 app.models.users.User），需含 id/phone_number/is_phone_verified 列
        execute: 是否实际写库（False 仅预演统计）
        batch_size: 每批提交条数
        limit: 最多扫描条数（0 表示全部，用于小范围验证）

    Returns:
        (stats, conflicts, invalids)
        stats: 统计字典（scanned/already_normalized/invalid/conflict/updated/would_update）
        conflicts: 重复账号冲突清单 [{id, phone, target}]
        invalids: 非法值清单 [{id, phone}]
    """
    from sqlalchemy import select
    from sqlalchemy.exc import IntegrityError

    if model is None:
        from app.models.users import User as model

    stats = {
        "scanned": 0,
        "already_normalized": 0,
        "invalid": 0,
        "conflict": 0,
        "updated": 0,
        "would_update": 0,
    }
    conflicts: List[dict] = []
    invalids: List[dict] = []

    last_id = 0
    pending: List = []

    def flush_batch():
        """批量提交挂起的更新；唯一约束冲突时回滚本批并逐条重试"""
        nonlocal pending
        if not pending:
            return
        if not execute:
            stats["would_update"] += len(pending)
            pending = []
            return
        batch = pending
        pending = []
        try:
            session.commit()
            stats["updated"] += len(batch)
        except IntegrityError:
            session.rollback()
            for row in batch:
                try:
                    session.add(row)
                    session.commit()
                    stats["updated"] += 1
                except IntegrityError:
                    session.rollback()
                    conflicts.append(
                        {"id": row.id, "phone": row.phone_number, "target": row.phone_number}
                    )
                    stats["conflict"] += 1

    while True:
        stmt = (
            select(model)
            .where(
                model.id > last_id,
                model.phone_number.isnot(None),
                model.phone_number != "",
                model.is_phone_verified == True,
            )
            .order_by(model.id)
            .limit(batch_size)
        )
        rows = session.execute(stmt).scalars().all()
        if not rows:
            break

        for row in rows:
            if limit and stats["scanned"] >= limit:
                flush_batch()
                return stats, conflicts, invalids
            stats["scanned"] += 1
            last_id = row.id

            kind, normalized = classify_phone(row.phone_number)
            if kind == "already":
                stats["already_normalized"] += 1
                continue
            if kind == "invalid":
                stats["invalid"] += 1
                invalids.append({"id": row.id, "phone": row.phone_number})
                logger.warning(
                    f"非法手机号(跳过，人工审核): id={row.id}, phone={mask_phone(row.phone_number)}"
                )
                continue

            # 预检冲突前先 flush，使本批内已修改记录对查询可见（未提交，可回滚）
            session.flush()
            dup = (
                session.execute(
                    select(model).where(
                        model.phone_number == normalized, model.id != row.id
                    )
                )
                .scalars()
                .first()
            )
            if dup:
                stats["conflict"] += 1
                conflicts.append(
                    {"id": row.id, "phone": row.phone_number, "target": normalized}
                )
                logger.warning(
                    f"重复账号(跳过，人工处理): id={row.id}, "
                    f"phone={mask_phone(row.phone_number)} 与 id={dup.id} "
                    f"归一化后同为 {mask_phone(normalized)}"
                )
                continue

            logger.info(
                f"待清洗: id={row.id}, phone={mask_phone(row.phone_number)} "
                f"-> {mask_phone(normalized)}"
            )
            row.phone_number = normalized
            pending.append(row)

        flush_batch()
        if len(rows) < batch_size:
            break

    return stats, conflicts, invalids


def main() -> bool:
    """命令行入口：预演（默认）或实际执行（--execute）"""
    parser = argparse.ArgumentParser(description="历史手机号数据归一化清洗")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="实际写入数据库（默认仅预演 dry-run）",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="每批提交条数（默认 500）",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="最多扫描条数（0=全部，用于小范围验证）",
    )
    args = parser.parse_args()

    if args.execute:
        confirm = input("即将实际写入数据库，请确认已完成备份！输入 'yes' 继续: ")
        if confirm.lower() != "yes":
            logger.info("操作已取消")
            return False

    from app.database import SessionLocal

    session = SessionLocal()
    try:
        stats, conflicts, invalids = scan_and_normalize(
            session,
            execute=args.execute,
            batch_size=args.batch_size,
            limit=args.limit,
        )
    except Exception as e:
        logger.error(f"清洗失败: {e}")
        return False
    finally:
        session.close()

    mode = "预演(dry-run)" if not args.execute else "执行"
    logger.info(f"========== 清洗{mode}报告 ==========")
    logger.info(f"扫描总数: {stats['scanned']}")
    logger.info(f"已归一化(跳过): {stats['already_normalized']}")
    logger.info(f"非法值(人工审核): {stats['invalid']}")
    logger.info(f"重复账号冲突(人工处理): {stats['conflict']}")
    if args.execute:
        logger.info(f"已更新: {stats['updated']}")
    else:
        logger.info(f"可清洗(未写入): {stats['would_update']}")
    for item in invalids:
        logger.info(f"  [非法] id={item['id']}, phone={mask_phone(item['phone'])}")
    for item in conflicts:
        logger.info(
            f"  [冲突] id={item['id']}, phone={mask_phone(item['phone'])} "
            f"-> 目标 {mask_phone(item['target'])}"
        )
    if not args.execute:
        logger.info("本次为预演，未写库；确认无误后使用 --execute 实际执行（脚本幂等，可重复执行）")
    return True


if __name__ == "__main__":
    main()
