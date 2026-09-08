"""医学合规违禁词库源数据（add-docs/13 §2–§3）"""

from typing import Dict, List, Tuple

from app.content_safety.tier import (
    LAYERED_STRATEGY_REMARK,
    resolve_action,
    resolve_tier,
)

FRAUD_PATTERN = "加V,私聊,返利,代购,兼职刷单,日结兼职,刷单,秒到,代发,引流,代付,博彩,加微,微信号"

MEDICAL_LEXICON: Dict[str, dict] = {
    "absolute_superlative": {
        "pattern": "顶级,顶尖,极致,终极,全网第一,全国第一,全球第一,行业第一,唯一,首选,首选款,独家,独家授权,独家配方,绝版,完美,完美无瑕,万能,永不,永久,永久有效,100%有效,百分百,全覆盖,全覆盖无死角,全网最低,最低价,史上最低,顶级工艺,最高端,榜首,冠军,最强,最优,无敌,顶级品质",
        "match_type": "keyword",
        "binding_level": "statutory",
        "regulation_ref": "广告法§9;广告法§16",
        "priority": 11,
    },
    "absolute_time_scale": {
        "pattern": "永久,终身,终生,永不褪色,永不损坏,永不反弹,全年最低价,十年不遇,千载难逢,仅此一次,仅此一天,永久保修,终身质保",
        "match_type": "keyword",
        "binding_level": "statutory",
        "regulation_ref": "广告法§9",
        "priority": 11,
    },
    "absolute_false_promise": {
        "pattern": "根治,根除,永不复发,100%痊愈,百分百见效,立刻见效,马上变好,一次根治,包治百病,神医,神药,祖传秘方",
        "match_type": "keyword",
        "binding_level": "statutory",
        "regulation_ref": "广告法§16;医疗广告办法§7",
        "priority": 11,
    },
    "cure_rate_quantified": {
        "pattern": r"(治愈|有效|康复|好转|痊愈)率?\s*[\d０-９]+[%％％]?|[\d０-９]+[%％％]?\s*(治愈|有效|康复|好转|痊愈)",
        "match_type": "regex",
        "binding_level": "statutory",
        "regulation_ref": "广告法§16;医疗广告办法§7",
        "priority": 11,
    },
    "medical_treatment_claim": {
        "pattern": "根治,治愈,抗癌,防癌,抗肿瘤,降血脂,修复病灶,根除炎症,缓解肿瘤,治疗失眠,治疗脚气,治疗皮肤病,治病,药用,药效,药食同疗",
        "match_type": "keyword",
        "binding_level": "statutory",
        "regulation_ref": "广告法§17;医疗广告办法§7",
        "priority": 12,
    },
    "cosmetic_medical_claim": {
        "pattern": "医美级,医用,药妆,祛斑,祛疤,祛痘根治,除皱永久,医美修复,淡化肿瘤,医疗修复,手术级,无菌医用,美白淡斑根治,根除痘印",
        "match_type": "keyword",
        "binding_level": "statutory",
        "regulation_ref": "广告法§17",
        "priority": 12,
    },
    "wellness_false_claim": {
        "pattern": "防癌,长寿,抗衰老,延年益寿,增强抵抗力,包治百病,预防新冠,预防流感,提高智商,增高,丰胸,壮阳,滋阴,速效壮阳,补肾根治",
        "match_type": "keyword",
        "binding_level": "statutory",
        "regulation_ref": "广告法§17",
        "priority": 12,
    },
    "medical_device_claim": {
        "pattern": "理疗仪,治疗仪,血糖仪,血压仪,医用冷敷贴,手术敷料,医用凝胶",
        "match_type": "keyword",
        "binding_level": "statutory",
        "regulation_ref": "广告法§17",
        "priority": 12,
    },
    "special_drug": {
        "pattern": "麻醉药品,精神药品,医疗用毒性药品,放射性药品,戒毒治疗,海洛因,冰毒,大麻,罂粟",
        "match_type": "keyword",
        "binding_level": "statutory",
        "regulation_ref": "广告法§15",
        "priority": 11,
    },
    "prescription_drug": {
        "pattern": "阿莫西林,奥司他韦,头孢,布洛芬缓释,二甲双胍,胰岛素,硝酸甘油,地西泮,吗啡,芬太尼,曲马多,左氧氟沙星,阿奇霉素,氯雷他定,洛索洛芬",
        "match_type": "keyword",
        "binding_level": "statutory",
        "regulation_ref": "广告法§15",
        "priority": 11,
    },
    "military_name": {
        "pattern": "解放军,武警,武警部队,部队医院",
        "match_type": "keyword",
        "binding_level": "statutory",
        "regulation_ref": "医疗广告办法§7",
        "priority": 12,
    },
    "porn_vulgar": {
        "pattern": "私处,私密,紧致,丰胸,性感露骨,大尺度,房事,助性,成人情趣,自慰,私处美白,私密护理,床上神器,夜间专用,情侣刺激,私密解压,魅惑,撩人,成人专用",
        "match_type": "porn",
        "binding_level": "platform",
        "regulation_ref": "科普十不得§8",
        "priority": 13,
    },
    "political_sensitive": {
        "pattern": "台独,港独,疆独,藏独,分裂国家,独立建国,反华组织,美化侵略,洗白战犯,否定历史,抹黑先烈,恶意调侃革命,造谣政务,抹黑公职人员",
        "match_type": "political",
        "binding_level": "statutory",
        "regulation_ref": "网络安全法;平台零容忍",
        "priority": 5,
    },
    "gambling": {
        "pattern": "赌博,下注,彩票,博彩,赔率,稳赢,必中,赌球,线上赌场,棋牌赚钱,刷单赌,非法彩票,内幕号码,稳赚不赔,赌博技巧,百家乐,德州扑克,线上棋牌",
        "match_type": "gambling",
        "binding_level": "statutory",
        "regulation_ref": "刑法;平台零容忍",
        "priority": 6,
    },
    "controlled_substance": {
        "pattern": "毒品,冰毒,海洛因,大麻,罂粟,止咳水,精神药品,违禁减肥药,三无激素药,麻醉剂,管制刀具,弓弩,弹弩,仿真枪,电击棍,管制器具,爆破器材,烟花爆竹私售",
        "match_type": "keyword",
        "binding_level": "statutory",
        "regulation_ref": "禁毒法;刑法",
        "priority": 6,
    },
    "financial_fraud": {
        "pattern": "保本,稳赚,零风险,高收益,日入过万,躺赚,复利翻倍,年化30%,内幕股票,荐股,带单,外汇操盘,虚拟货币挖矿,币圈,比特币,以太坊,资金盘,私募基金代投",
        "match_type": "keyword",
        "binding_level": "platform",
        "regulation_ref": "广告法;金融监管",
        "priority": 14,
    },
    "mlm_fraud": {
        "pattern": "拉人头,裂变返利,层级分红,躺赚,一夜暴富,代理囤货,倍增收益,创业暴富,月入十万",
        "match_type": "keyword",
        "binding_level": "platform",
        "regulation_ref": "禁止传销条例",
        "priority": 14,
    },
    "loan_fraud": {
        "pattern": "无息贷款,零门槛放款,洗白征信,消除逾期,代办信用卡,私人放款,套路贷",
        "match_type": "keyword",
        "binding_level": "platform",
        "regulation_ref": None,
        "priority": 14,
    },
    "abuse_discrimination": {
        "pattern": "脑残,去死,地域黑,地域歧视,性别歧视,容貌羞辱,残疾人嘲讽,种族歧视,性别对立,职业羞辱,身材羞辱,打架,报复,伤人,殴打,自杀,自残,跳楼,轻生教程,教唆离家出走",
        "match_type": "keyword",
        "binding_level": "platform",
        "regulation_ref": "平台社区规范",
        "priority": 15,
    },
    "food_false_claim": {
        "pattern": "防癌,降三高,减肥特效药,减脂根治,代餐瘦20斤,儿童增高,增强记忆力,治病,排毒,排宿便,根治便秘,无菌无添加,零防腐剂",
        "match_type": "keyword",
        "binding_level": "statutory",
        "regulation_ref": "广告法§17",
        "priority": 12,
    },
    "baby_false_claim": {
        "pattern": "补脑,提高智力,根治湿疹,长高,增强免疫力,治疗黄疸,根治红屁股,医用护臀",
        "match_type": "keyword",
        "binding_level": "statutory",
        "regulation_ref": "广告法§17",
        "priority": 12,
    },
    "home_false_claim": {
        "pattern": "杀菌99.999%,根除甲醛,永久除螨,根治异味,一秒除甲醛",
        "match_type": "keyword",
        "binding_level": "statutory",
        "regulation_ref": "广告法§17",
        "priority": 12,
    },
    "counterfeit_infringement": {
        "pattern": "仿大牌,平替正品,原厂尾单,海关扣押货,走私货,高仿,A货,原版复刻,盗用商标,明星同款诱导",
        "match_type": "keyword",
        "binding_level": "platform",
        "regulation_ref": "商标法;反不正当竞争法",
        "priority": 14,
    },
    "false_endorsement": {
        "pattern": "国检第一,国家级认证,院士研发,三甲医院推荐,专家背书,权威机构唯一推荐,明星代言,患者亲测,康复案例,疗效证明",
        "match_type": "keyword",
        "binding_level": "statutory",
        "regulation_ref": "广告法§16;医疗广告办法§7",
        "priority": 12,
    },
    "privacy_gray": {
        "pattern": "查开房记录,查征信,查手机号定位,调取聊天记录,人肉搜索,买卖身份证,买卖银行卡,买卖手机号",
        "match_type": "keyword",
        "binding_level": "statutory",
        "regulation_ref": "个人信息保护法",
        "priority": 13,
    },
    "cheat_gray": {
        "pattern": "刷单,刷赞,刷播放,刷销量,脚本外挂,游戏作弊,代解封账号,代过实名认证,破解软件",
        "match_type": "keyword",
        "binding_level": "platform",
        "regulation_ref": "平台规范",
        "priority": 14,
    },
    "cosmetic_surgery": {
        "pattern": "整容,隆鼻,抽脂,割双眼皮,微创手术,注射玻尿酸,肉毒素,整形修复,手术无痕,永久塑形,溶脂针,水光针",
        "match_type": "keyword",
        "binding_level": "statutory",
        "regulation_ref": "医疗广告办法§7",
        "priority": 12,
    },
    "platform_circumvention": {
        "pattern": "内部价,内部通道,内部优惠券,私下转账,微信交易,私发链接,绕过平台,线下付款,刷单返现,好评返现,五星返利,强制好评",
        "match_type": "keyword",
        "binding_level": "platform",
        "regulation_ref": "平台交易规范",
        "priority": 30,
    },
    "superstition": {
        "pattern": "算命,占卜,看风水,改运,符咒,跳大神,算命预测,改命,开光招财,辟邪神器,封建迷信治病,塔罗预测运势",
        "match_type": "keyword",
        "binding_level": "statutory",
        "regulation_ref": "医疗广告办法§7;科普十不得§8",
        "priority": 13,
    },
}

FRAMEWORK_RULES: List[Tuple[str, str, str, int, str, str]] = [
    ("framework_url", "url", "builtin", 10, "platform", "科普十不得§2"),
    ("framework_contact", "contact", "builtin", 20, "platform", "科普十不得§2"),
    ("framework_fraud", "fraud", FRAUD_PATTERN, 30, "platform", "科普十不得§2"),
]

# DROP 审计：禁止再次进入 pattern 的裸词（验收/回归用，对齐 wechat-v1 词库治理）
DROPPED_BARE_KEYWORDS = (
    "最",
    "第一",
    "天花板",
    "治疗",
    "消炎",
    "消肿",
    "降压",
    "降糖",
    "止痛",
    "祛湿",
    "养胃",
    "护肝",
    "抗过敏",
    "处方",
    "麻醉",
    "嫩",
    "裸",
    "露",
    "增大",
    "延时",
    "丰满",
    "诱惑",
    "垃圾",
    "优惠",
    "兼职",
    "水货",
)


def resolve_severity(category: str, binding_level: str) -> str:
    if binding_level == "statutory":
        return "critical"
    if category == "platform_circumvention":
        return "medium"
    return "high"


def build_medical_rules(text_field_matrix: dict[str, List[str]]) -> List[dict]:
    """按 scene × field 矩阵生成医学合规规则（含分档 action / 低档弱 seed）"""
    rules: List[dict] = []
    for scene, fields in text_field_matrix.items():
        for field in fields:
            tier = resolve_tier(scene, field)
            for category, meta in MEDICAL_LEXICON.items():
                binding = meta["binding_level"]
                action = resolve_action(category, tier)
                enabled = action is not None
                rules.append(
                    {
                        "rule_name": f"{scene}-{field}-{category}",
                        "scene": scene,
                        "target_field": field,
                        "match_type": meta["match_type"],
                        "pattern": meta["pattern"],
                        "action": action or "block",
                        "severity": resolve_severity(category, binding),
                        "priority": meta["priority"],
                        "binding_level": binding,
                        "rule_category": category,
                        "regulation_ref": meta.get("regulation_ref"),
                        "enabled": enabled,
                        "remark": f"{LAYERED_STRATEGY_REMARK}；{category}；档{tier}",
                    }
                )
            for fw_name, match_type, pattern, priority, binding_level, regulation_ref in FRAMEWORK_RULES:
                action = resolve_action(fw_name, tier)
                enabled = action is not None
                rules.append(
                    {
                        "rule_name": f"{scene}-{field}-{fw_name}",
                        "scene": scene,
                        "target_field": field,
                        "match_type": match_type,
                        "pattern": pattern,
                        "action": action or "block",
                        "severity": resolve_severity(fw_name, binding_level),
                        "priority": priority,
                        "binding_level": binding_level,
                        "rule_category": fw_name,
                        "regulation_ref": regulation_ref,
                        "enabled": enabled,
                        "remark": f"{LAYERED_STRATEGY_REMARK}；{fw_name}；档{tier}",
                    }
                )
    return rules
