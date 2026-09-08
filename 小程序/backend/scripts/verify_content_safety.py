#!/usr/bin/env python3
"""内容安全模块离线自测（无需数据库，对照 add-docs/12/13/12-13）"""

import importlib.util
import sys
import types
import uuid
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
LC = ROOT / "backend" / "live_core_service"
LC_CS = LC / "app" / "content_safety"


def _load_submodule(mod_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    sys.path.insert(0, str(LC))
    app_pkg = types.ModuleType("app")
    cs_pkg = types.ModuleType("app.content_safety")
    sys.modules["app"] = app_pkg
    sys.modules["app.content_safety"] = cs_pkg

    tier = _load_submodule("app.content_safety.tier", LC_CS / "tier.py")
    whitelist = _load_submodule("app.content_safety.whitelist", LC_CS / "whitelist.py")
    data = _load_submodule("app.content_safety.medical_lexicon_data", LC_CS / "medical_lexicon_data.py")
    _load_submodule("app.content_safety.schemas", LC_CS / "schemas.py")
    engine = _load_submodule("app.content_safety.engine", LC_CS / "engine.py")

    live_matrix = {
        "message": ["content"],
        "room_title": ["title"],
        "room_description": ["description"],
        "room_tab": ["tab_key", "title", "text_content"],
        "search_query": ["keyword"],
    }
    live_rules = data.build_medical_rules(live_matrix)
    user_rules = data.build_medical_rules({"nickname": ["nickname", "bio"]})

    checks = []

    def ok(check_name: str, cond: bool, detail: str = ""):
        checks.append((check_name, cond, detail))

    ok("MEDICAL_LEXICON 29 类", len(data.MEDICAL_LEXICON) == 29)
    ok("FRAMEWORK_RULES 3 类", len(data.FRAMEWORK_RULES) == 3)
    ok("live_core 224 条", len(live_rules) == 224, f"got {len(live_rules)}")
    ok("users 64 条", len(user_rules) == 64, f"got {len(user_rules)}")
    ok(
        "规则命名 {scene}-{field}-{category}",
        all(
            r["rule_name"] == f"{r['scene']}-{r['target_field']}-{r['rule_category']}"
            for r in live_rules[:5]
        ),
    )
    ok(
        "statutory severity=critical",
        all(r["severity"] == "critical" for r in live_rules if r["binding_level"] == "statutory"),
    )
    ok("FRAUD 无优惠裸词", "优惠" not in {p.strip() for p in data.FRAUD_PATTERN.split(",")})
    ok("A 档绝对化为 warn", tier.resolve_action("absolute_superlative", "A") == "warn")
    ok("D 档绝对化禁用", tier.resolve_action("absolute_superlative", "D") is None)

    def enabled_ns(scene: str, field: str):
        built = data.build_medical_rules({scene: [field]})
        return [
            SimpleNamespace(id=uuid.uuid4(), **{k: v for k, v in r.items() if k != "remark"})
            for r in built
            if r["enabled"]
        ]

    d, matched, _ = engine.evaluate_field(
        enabled_ns("room_title", "title"), "title", "这是我第一次直播"
    )
    ok("第一次直播 allow", d == "allow" and not matched)

    d, matched, _ = engine.evaluate_field(enabled_ns("message", "content"), "content", "完美收官")
    ok("完美收官白名单 allow", d == "allow" and not matched)

    d, matched, _ = engine.evaluate_field(enabled_ns("message", "content"), "content", "包治百病")
    ok("包治百病 block", d == "block" and bool(matched))

    d, matched, _ = engine.evaluate_field(
        enabled_ns("room_title", "title"), "title", "全网第一款科普课"
    )
    ok("全网第一 A=warn", d == "warn" and bool(matched))

    d, matched, _ = engine.evaluate_field(enabled_ns("message", "content"), "content", "加V私聊返利")
    ok("加V私聊返利 block", d == "block")

    d, matched, _ = engine.evaluate_field(enabled_ns("message", "content"), "content", "台独")
    ok("台独 block", d == "block")

    d, matched, _ = engine.evaluate_field(enabled_ns("message", "content"), "content", "请做好垃圾分类")
    ok("垃圾分类 allow", d == "allow")

    d, matched, _ = engine.evaluate_field(enabled_ns("message", "content"), "content", "延时摄影分享")
    ok("延时摄影 allow", d == "allow")

    ok(
        "白名单含第一次",
        "第一次" in whitelist.CONTENT_SAFETY_WHITELIST["absolute_superlative"],
    )

    failed = [c for c in checks if not c[1]]
    print("=" * 60)
    print("内容安全离线自测（add-docs/12 + 13 + 12-13 分层）")
    print("=" * 60)
    for check_name, passed, detail in checks:
        mark = "PASS" if passed else "FAIL"
        extra = f" ({detail})" if detail and not passed else ""
        print(f"  [{mark}] {check_name}{extra}")
    print("=" * 60)
    if failed:
        print(f"失败 {len(failed)} / {len(checks)}")
        return 1
    print(f"全部通过 {len(checks)} 项")
    return 0


if __name__ == "__main__":
    sys.exit(main())
