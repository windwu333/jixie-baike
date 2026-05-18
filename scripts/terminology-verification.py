#!/usr/bin/env python3
"""术语翻译校审 — 逐项对照权威词典验证中英文术语

输入: mech-terminology-v4.json (5049 terms + 4449 extras)
参考: mech-supplement.json, seed_dictionary (v3/v2), canonical translations
输出: knowledge-base/terminology-verification-report.json + 待处理问题清单

Pipeline: 构建参考词典 → 交叉验证 → 分类标记 → 生成报告
"""
import json, re, sys
from pathlib import Path
from collections import defaultdict, Counter

BASE = Path(__file__).parent.parent
KB = BASE / "knowledge-base"

# ── 1. 规范翻译规则 (canonical translations) ──────────────────────────
# 这些是从权威标准（GB/T, 机械工程名词等）确认的规范翻译
# 格式: { "en": "标准中文" }
CANONICAL = {
    # 力学与强度
    "torque": "转矩",
    "torsion": "扭转",
    "torsional stress": "扭转应力",
    "bending": "弯曲",
    "bending moment": "弯矩",
    "shear": "剪切",
    "shear stress": "切应力",
    "shear strain": "切应变",
    "normal stress": "正应力",
    "principal stress": "主应力",
    "stress concentration": "应力集中",
    "stress intensity": "应力强度",
    "stress tensor": "应力张量",
    "strain tensor": "应变张量",
    "fatigue": "疲劳",
    "fatigue strength": "疲劳强度",
    "fatigue life": "疲劳寿命",
    "fatigue crack": "疲劳裂纹",
    "creep": "蠕变",
    "yield": "屈服",
    "yield strength": "屈服强度",
    "yield point": "屈服点",
    "ultimate strength": "强度极限",
    "tensile strength": "抗拉强度",
    "compressive strength": "抗压强度",
    "elastic modulus": "弹性模量",
    "modulus of elasticity": "弹性模量",
    "young's modulus": "杨氏模量",
    "shear modulus": "切变模量",
    "poisson's ratio": "泊松比",
    "hardness": "硬度",
    "toughness": "韧性",
    "ductility": "延性",
    "brittleness": "脆性",
    "malleability": "可锻性",
    "resilience": "回弹能力",

    # 齿轮与传动 (GB/T 10853-2008 规范)
    "pitch": "齿距",
    "pitch circle": "分度圆",
    "pitch diameter": "分度圆直径",
    "module": "模数",
    "gear ratio": "传动比",
    "backlash": "侧隙",
    "addendum": "齿顶高",
    "dedendum": "齿根高",
    "clearance": "顶隙",
    "tooth profile": "齿廓",
    "involute": "渐开线",
    "cycloid": "摆线",
    "trochoid": "次摆线",
    "helix angle": "螺旋角",
    "pressure angle": "压力角",
    "contact ratio": "重合度",
    "pitting": "点蚀",
    "pitting resistance": "接触强度",
    "scoring": "胶合",
    "spalling": "剥落",
    "gear train": "轮系",
    "planetary gear": "行星齿轮",
    "sun gear": "太阳轮",
    "ring gear": "齿圈",
    "planet carrier": "行星架",

    # 轴承
    "plain bearing": "滑动轴承",
    "rolling bearing": "滚动轴承",
    "ball bearing": "球轴承",
    "roller bearing": "滚子轴承",
    "thrust bearing": "推力轴承",
    "journal bearing": "径向滑动轴承",
    "raceway": "滚道",
    "cage": "保持架",

    # 热处理 (GB/T 7232 规范)
    "annealing": "退火",
    "normalizing": "正火",
    "quenching": "淬火",
    "tempering": "回火",
    "aging": "时效",
    "case hardening": "表面硬化",
    "carburizing": "渗碳",
    "nitriding": "渗氮",
    "carbonitriding": "碳氮共渗",
    "induction hardening": "感应淬火",
    "flame hardening": "火焰淬火",
    "solution treatment": "固溶处理",
    "precipitation hardening": "沉淀硬化",
    "hardenability": "淬透性",

    # 焊接 (GB/T 3375 规范)
    "welding": "焊接",
    "brazing": "硬钎焊",
    "soldering": "软钎焊",
    "arc welding": "电弧焊",
    "gas welding": "气焊",
    "resistance welding": "电阻焊",
    "friction welding": "摩擦焊",
    "ultrasonic welding": "超声波焊",
    "laser welding": "激光焊",
    "electron beam welding": "电子束焊",
    "butt joint": "对接接头",
    "lap joint": "搭接接头",
    "fillet weld": "角焊缝",
    "groove weld": "坡口焊缝",
    "heat affected zone": "热影响区",
    "weld metal": "焊缝金属",
    "base metal": "母材",
    "filler metal": "填充金属",
    "flux": "焊剂",
    "slag": "熔渣",

    # 锻造
    "forging": "锻造",
    "die forging": "模锻",
    "open die forging": "自由锻",
    "closed die forging": "闭式模锻",
    "hot forging": "热锻",
    "cold forging": "冷锻",
    "warm forging": "温锻",
    "upsetting": "镦粗",
    "extrusion": "挤压",
    "swaging": "旋转锻造",

    # 铸造 (GB/T 5611 规范)
    "casting": "铸造",
    "sand casting": "砂型铸造",
    "die casting": "压铸",
    "investment casting": "熔模铸造",
    "centrifugal casting": "离心铸造",
    "continuous casting": "连铸",
    "mold": "铸型",
    "pattern": "模样",
    "core": "型芯",
    "riser": "冒口",
    "runner": "横浇道",
    "gate": "内浇口",
    "shrinkage": "缩孔",
    "porosity": "气孔",

    # 机械制图与CAD (GB/T 14689 等)
    "orthographic projection": "正投影",
    "isometric view": "轴测图",
    "section view": "剖视图",
    "detail view": "局部放大图",
    "exploded view": "爆炸图",
    "auxiliary view": "辅助视图",
    "datum": "基准",
    "tolerance": "公差",
    "dimension": "尺寸",
    "surface finish": "表面粗糙度",
    "first angle projection": "第一角投影",
    "third angle projection": "第三角投影",
    "scale": "比例",
    "title block": "标题栏",
    "bill of materials": "明细栏",

    # 热工与流体
    "thermodynamics": "热力学",
    "heat transfer": "传热",
    "conduction": "热传导",
    "convection": "热对流",
    "radiation": "热辐射",
    "fluid mechanics": "流体力学",
    "viscosity": "黏度",
    "laminar flow": "层流",
    "turbulent flow": "湍流",
    "boundary layer": "边界层",
    "bernoulli's principle": "伯努利原理",
    "reynolds number": "雷诺数",
    "mach number": "马赫数",
    "enthalpy": "焓",
    "entropy": "熵",
    "specific heat": "比热容",
    "thermal conductivity": "导热系数",
    "thermal expansion": "热膨胀",

    # 机电
    "sensor": "传感器",
    "actuator": "执行器",
    "transducer": "换能器",
    "servo motor": "伺服电动机",
    "stepper motor": "步进电动机",
    "encoder": "编码器",
    "solenoid": "电磁铁",
    "relay": "继电器",
    "contactor": "接触器",
    "potentiometer": "电位器",
    "thermocouple": "热电偶",
    "strain gauge": "应变片",
    "accelerometer": "加速度计",
    "proximity sensor": "接近传感器",
    "limit switch": "限位开关",
    "plc": "可编程控制器",
    "microcontroller": "微控制器",

    # 材料
    "steel": "钢",
    "cast iron": "铸铁",
    "carbon steel": "碳钢",
    "alloy steel": "合金钢",
    "stainless steel": "不锈钢",
    "tool steel": "工具钢",
    "aluminum alloy": "铝合金",
    "copper alloy": "铜合金",
    "titanium alloy": "钛合金",
    "composite material": "复合材料",
    "ceramic": "陶瓷",
    "polymer": "聚合物",
    "elastomer": "弹性体",
    "corrosion": "腐蚀",
    "oxidation": "氧化",

    # 动力机械
    "internal combustion engine": "内燃机",
    "gas turbine": "燃气轮机",
    "steam turbine": "汽轮机",
    "compressor": "压缩机",
    "turbine": "涡轮",
    "nozzle": "喷嘴",
    "propeller": "螺旋桨",

    # 液压气动
    "hydraulic system": "液压系统",
    "pneumatic system": "气动系统",
    "pump": "泵",
    "valve": "阀",
    "cylinder": "缸",
    "piston": "活塞",
    "seal": "密封件",
    "accumulator": "蓄能器",
    "filter": "过滤器",
    "regulator": "调压阀",
    "actuator": "执行元件",

    # 测量
    "caliper": "卡尺",
    "micrometer": "千分尺",
    "gauge": "量规",
    "indicator": "指示表",
    "surface plate": "平板",
    "gage block": "量块",
    "coordinate measuring machine": "坐标测量机",
}


def load_json(path):
    """Load JSON, handle various formats"""
    if not path.exists():
        return None
    data = json.loads(path.read_bytes())
    return data


def build_reference_dict():
    """Build authoritative reference dictionary from trusted sources"""
    ref = {}  # en_lower → { zh, source, category, description }

    # 1. Supplement (highest quality, hand-curated)
    sup = load_json(KB / "mech-supplement.json")
    if sup and isinstance(sup, list):
        for t in sup:
            en = t.get("en", "").strip().lower()
            zh = t.get("zh", "").strip()
            if en and zh:
                if en not in ref:
                    ref[en] = {"zh": zh, "source": "mech-supplement",
                               "category": t.get("category", ""),
                               "description": t.get("description", "")}

    # 2. v3/v4 seed terms (hand-curated seed dictionary)
    for ver in ("v3", "v2"):
        f = KB / f"mech-terminology-{ver}.json"
        if not f.exists():
            continue
        data = load_json(f)
        terms = data.get("terms", []) if isinstance(data, dict) else data
        for t in terms:
            src = t.get("source", "")
            if src != "seed" and src != "seed_dictionary":
                continue
            en = t.get("en", "").strip().lower()
            zh = t.get("zh", "").strip()
            if en and zh and en not in ref:
                ref[en] = {"zh": zh, "source": f"seed_dictionary_{ver}",
                           "category": t.get("category", ""),
                           "description": t.get("description", "")}

    # 3. v4 terms with source="seed"
    v4 = load_json(KB / "mech-terminology-v4.json")
    if v4:
        for t in v4.get("terms", []):
            if t.get("source") != "seed":
                continue
            en = t.get("en", "").strip().lower()
            zh = t.get("zh", "").strip()
            if en and zh and en not in ref:
                ref[en] = {"zh": zh, "source": "seed_v4",
                           "category": t.get("category", ""),
                           "description": t.get("description", "")}

    # 4. Canonical translations (highest override authority)
    for en_lower, zh_std in CANONICAL.items():
        ref[en_lower] = {"zh": zh_std, "source": "canonical_gbt",
                         "category": "", "description": "GB/T 标准规范翻译"}

    return ref


def evaluate_translation_quality(term_entry, ref):
    """Evaluate a single term's zh translation quality.

    Returns: (quality_label, detail_dict)
    quality_label: 'verified', 'minor_deviation', 'suspicious', 'no_reference', 'garbage'
    """
    en = term_entry.get("en", "").strip()
    zh = term_entry.get("zh", "").strip()
    en_lower = en.lower()

    # Common mixed-language abbreviations that are standard in Chinese engineering
    COMMON_ABBREV = {"3d", "cad", "cae", "cam", "capp", "pdm", "plm", "erp",
                     "fea", "cmm", "cnc", "nc", "edm", "plc", "pcl", "pcb",
                     "led", "lcd", "ccd", "gps", "gprs", "wifi", "usb",
                     "hvac", "mep", "iso", "ansi", "din", "gb", "jb",
                     "y", "x", "z", "u", "v", "w"}
    # Known abbreviations commonly used in Chinese text
    COMMON_PREFIX = {"3d": "三维", "cad": "计算机辅助设计", "cae": "计算机辅助工程",
                     "cam": "计算机辅助制造", "cnc": "数控", "fea": "有限元",
                     "plc": "可编程逻辑控制器", "hvac": "暖通空调"}

    # Check for garbage zh
    if not zh:
        return "garbage", {"reason": "缺少中文翻译"}
    if zh == en_lower:
        return "garbage", {"reason": "中文翻译仅为英文原文小写"}

    import re as _re

    # Check if zh is just en (case-insensitive, ignoring punctuation/spaces)
    zh_clean = _re.sub(r'[\s\-_.,;:!?()\[\]{}\'"]', '', zh)
    en_clean = _re.sub(r'[\s\-_.,;:!?()\[\]{}\'"]', '', en_lower)
    if zh_clean.lower() == en_clean.lower():
        return "garbage", {"reason": "中文仅为英文原文(无实际翻译)"}

    # Extract ASCII-only words from zh
    zh_ascii_words = _re.findall(r'\b[a-zA-Z]+\b', zh)
    zh_ascii_letters = [w for w in zh_ascii_words
                        if w.lower() not in COMMON_ABBREV
                        and not _re.match(r'^(and|or|the|of|for|in|on|at|with|to|by|is|are|a|an)$', w.lower())]

    # Has real ASCII words that aren't common abbreviations
    if zh_ascii_letters:
        return "partial_translation", {"reason": f"中文含未处理英文词: {', '.join(zh_ascii_letters[:3])}",
                                       "ascii_words": zh_ascii_letters}

    # Check for obviously machine-translated structure (e.g., "X的Y" where X is English concept)
    zh_prefix = zh.split("的")[0] if "的" in zh else ""
    if zh_prefix and len(zh_prefix) >= 3 and len(zh_prefix) <= 15:
        zh_prefix_ascii = _re.findall(r'[a-zA-Z]', zh_prefix)
        # If first part before 的 has ASCII, it's partial machine translation
        if zh_prefix_ascii:
            return "garbage", {"reason": f"机翻残留: '{zh}'含未译英文前缀"}

    # Check against reference
    if en_lower in ref:
        ref_entry = ref[en_lower]
        ref_zh = ref_entry["zh"]
        if zh == ref_zh:
            return "verified", {"source": ref_entry["source"],
                                "ref_zh": ref_zh}
        else:
            # Check if it's a reasonable synonym
            return "minor_deviation", {"source": ref_entry["source"],
                                       "ref_zh": ref_zh,
                                       "current_zh": zh,
                                       "reason": f"翻译与权威参考不一致: 当前'{zh}' vs 标准'{ref_zh}'"}

    # Check for partial matches (term contains a known sub-term)
    for ref_en, ref_entry in ref.items():
        # Check if reference English term is contained in this term
        words_en = set(en_lower.split())
        ref_words = set(ref_en.split())
        common = words_en & ref_words
        if len(common) >= 1 and len(common) >= min(len(words_en), len(ref_words)):
            # The zh might contain the reference zh
            if ref_entry["zh"] in zh:
                return "verified", {"source": ref_entry["source"],
                                    "ref_zh": ref_entry["zh"],
                                    "note": "局部匹配(子术语)"}

    # No match in reference, but zh looks like real Chinese
    # Check zh looks like legitimate mechanical term
    mech_chars = ["力", "度", "量", "机", "器", "械",
                  "热", "电", "材", "金", "钢", "铁",
                  "齿", "轴", "轮", "焊", "铸", "锻",
                  "压", "切", "削", "磨", "钻", "铣",
                  "车", "孔", "面", "线", "角", "形",
                  "件", "表", "套", "环", "链", "带",
                  "阀", "泵", "缸", "管", "流", "体",
                  "控", "制", "传", "动", "转", "速",
                  "弹", "簧", "密", "封", "承", "杆",
                  "板", "层", "涂", "镀", "蚀", "燃"]
    if any(mc in zh for mc in mech_chars):
        return "suspicious", {"reason": "无权威参考对照，但术语形态合理",
                              "confidence": "low"}
    else:
        # Try common Chinese single-character terms (elements, basic concepts)
        common_single = {"钢", "铁", "铜", "铝", "锌", "锡", "铅", "金", "银",
                         "碳", "硅", "锰", "铬", "镍", "钼", "钛", "钒", "钨",
                         "钴", "氮", "氧", "氢", "氦", "氩", "锂", "铍", "硼"}
        if len(zh) == 1 and zh in common_single:
            return "verified", {"source": "common_element",
                                "note": f"常见化学元素/材料: {zh}"}
        return "suspicious", {"reason": "无权威参考对照，需人工审核",
                              "confidence": "high"}


def analyze_v4_terms():
    """Main analysis pipeline"""
    v4 = load_json(KB / "mech-terminology-v4.json")
    if not v4:
        print("ERROR: mech-terminology-v4.json not found", file=sys.stderr)
        return

    ref = build_reference_dict()
    print(f"参考词典: {len(ref)} 条权威术语", file=sys.stderr)

    terms = v4.get("terms", [])
    extras = v4.get("extracted_extras", [])

    results = {
        "meta": {
            "reference_dict_size": len(ref),
            "total_terms": len(terms),
            "total_extras": len(extras),
            "verification_date": "2026-05-18",
        },
        "reference": {
            "canonical_gbt": len(CANONICAL),
            "mech_supplement": 86,
            "seed_dictionary": 645,
        },
        "terms": [],
        "extras_summary": {},
        "issues": [],
        "stats": {},
    }

    # ── Analyze 5049 terms ──
    quality_counts = Counter()
    issues = []
    deviated_terms = []
    garbage_terms = []
    suspicious_terms = []
    verified_terms = []

    for t in terms:
        en = t.get("en", "").strip()
        zh = t.get("zh", "").strip()
        cat = t.get("category", "")
        src = t.get("source", "")

        q, detail = evaluate_translation_quality(t, ref)
        quality_counts[q] += 1

        entry = {
            "en": en,
            "zh": zh,
            "category": cat,
            "source": src,
            "quality": q,
            "detail": detail,
        }
        results["terms"].append(entry)

        if q == "minor_deviation":
            deviated_terms.append(entry)
            issues.append({
                "type": "terminology_deviation",
                "severity": "medium",
                "term": en,
                "current_zh": zh,
                "standard_zh": detail.get("ref_zh", ""),
                "source": detail.get("source", ""),
                "category": cat,
                "recommendation": f"将'{zh}'改为'{detail.get('ref_zh','')}'以符合{detail.get('source','')}规范",
            })
        elif q == "garbage":
            garbage_terms.append(entry)
            issues.append({
                "type": "garbage_translation",
                "severity": "critical" if src != "wikipedia" else "high",
                "term": en,
                "current_zh": zh,
                "reason": detail.get("reason", ""),
                "category": cat,
                "source": src,
                "recommendation": "需重新翻译",
            })
        elif q == "partial_translation":
            garbage_terms.append(entry)
            issues.append({
                "type": "partial_translation",
                "severity": "high",
                "term": en,
                "current_zh": zh,
                "reason": detail.get("reason", ""),
                "category": cat,
                "source": src,
                "recommendation": "需补充完整中文翻译",
            })
        elif q == "suspicious" and detail.get("confidence") == "high":
            suspicious_terms.append(entry)
            issues.append({
                "type": "unverified_term",
                "severity": "medium",
                "term": en,
                "current_zh": zh,
                "reason": detail.get("reason", ""),
                "category": cat,
                "source": src,
                "recommendation": "需人工确认翻译准确性",
            })

    results["stats"]["term_quality"] = dict(quality_counts.most_common())
    results["stats"]["total_issues"] = len(issues)
    results["issues"] = issues
    results["deviated_terms"] = deviated_terms
    results["garbage_terms"] = garbage_terms
    results["suspicious_terms"] = suspicious_terms

    # ── Analyze 4449 extras ──
    import re as _re
    COMMON_ABBREV = {"3d", "cad", "cae", "cam", "capp", "pdm", "plm", "erp",
                     "fea", "cmm", "cnc", "nc", "edm", "plc", "pcl", "pcb",
                     "led", "lcd", "ccd", "gps", "gprs", "wifi", "usb",
                     "hvac", "mep", "iso", "ansi", "din", "gb", "jb"}
    extras_good = 0
    extras_bad = 0
    extras_source_counts = Counter()
    for e in extras:
        zh = e.get("zh", "").strip()
        en = e.get("en", "").strip()
        esrc = e.get("source", "")
        extras_source_counts[esrc] += 1

        if not zh:
            extras_bad += 1
            continue
        # Check if zh is good (pure Chinese, possibly with common abbreviations)
        zh_ascii_words = _re.findall(r'\b[a-zA-Z]+\b', zh)
        real_ascii = [w for w in zh_ascii_words
                      if w.lower() not in COMMON_ABBREV]
        zh_clean = _re.sub(r'[\s\-_.,;:!?()\[\]{}]', '', zh)
        en_clean = _re.sub(r'[\s\-_.,;:!?()\[\]{}]', '', en.lower())
        if zh_clean == en_clean:
            extras_bad += 1
        elif real_ascii and len(zh) < 10:
            extras_bad += 1
        elif len(zh) >= 2:
            extras_good += 1
        else:
            extras_bad += 1

    results["extras_summary"] = {
        "total": len(extras),
        "good_zh": extras_good,
        "bad_zh": extras_bad,
        "source_distribution": dict(extras_source_counts.most_common()),
        "note": f"{extras_bad}/{len(extras)} 条需重新翻译（机翻质量差）",
    }

    # ── Category-level summary ──
    cat_quality = defaultdict(Counter)
    for entry in results["terms"]:
        cat_quality[entry["category"]][entry["quality"]] += 1

    results["category_quality"] = {
        cat: dict(counter.most_common())
        for cat, counter in sorted(cat_quality.items())
    }

    # ── Source-level summary ──
    src_quality = defaultdict(Counter)
    for entry in results["terms"]:
        src_quality[entry["source"]][entry["quality"]] += 1

    results["source_quality"] = {
        src: dict(counter.most_common())
        for src, counter in sorted(src_quality.items())
    }

    return results


def generate_issue_list(results):
    """Generate the 待处理问题清单 in structured format"""
    issues = results["issues"]

    # Group by severity
    by_severity = defaultdict(list)
    for iss in issues:
        by_severity[iss["severity"]].append(iss)

    # Generate report
    report_lines = []
    report_lines.append("# 机械术语翻译校审 — 待处理问题清单\n")
    report_lines.append(f"校审日期: 2026-05-18\n")
    report_lines.append(f"参考词典: {results['meta']['reference_dict_size']} 条权威术语\n")
    report_lines.append(f"总术语数: {results['meta']['total_terms']} (terms) + {results['meta']['total_extras']} (extras)\n")
    report_lines.append(f"\n---\n")

    # Summary
    report_lines.append("## 总体统计\n\n")
    qs = results["stats"]["term_quality"]
    total = sum(qs.values())
    report_lines.append(f"| 质量等级 | 数量 | 占比 |\n")
    report_lines.append(f"|---------|------|------|\n")
    quality_labels = {"verified": "✅ 已验证",
                      "suspicious": "❓ 需审核",
                      "minor_deviation": "⚠️ 术语偏差",
                      "garbage": "🚫 未翻译",
                      "partial_translation": "⚠️ 部分翻译"}
    for q in ["verified", "suspicious", "minor_deviation", "partial_translation", "garbage"]:
        n = qs.get(q, 0)
        if n == 0:
            continue
        pct = n / total * 100 if total > 0 else 0
        label = quality_labels.get(q, q)
        report_lines.append(f"| {label} | {n} | {pct:.1f}% |\n")

    report_lines.append(f"\n**问题总数: {len(issues)}**\n")
    report_lines.append(f"\n---\n")

    # Critical issues
    critical = by_severity.get("critical", [])
    if critical:
        report_lines.append(f"## 🔴 严重问题 (CRITICAL) — 翻译垃圾需全部重做\n\n")
        report_lines.append(f"共 {len(critical)} 条\n\n")
        report_lines.append(f"| 英文术语 | 当前翻译 | 分类 | 来源 | 建议 |\n")
        report_lines.append(f"|---------|---------|------|------|------|\n")
        for iss in critical[:50]:  # cap display
            report_lines.append(f"| {iss['term']} | {iss['current_zh']} | {iss['category']} | {iss['source']} | {iss['recommendation']} |\n")
        if len(critical) > 50:
            report_lines.append(f"| ... 另有 {len(critical)-50} 条 | 详见完整数据文件 | | | |\n")

    report_lines.append(f"\n---\n")

    # High issues - partial translations
    partial = by_severity.get("high", [])
    if partial:
        report_lines.append(f"## 🟡 部分翻译 (HIGH) — 含未翻译英文字词\n\n")
        report_lines.append(f"共 {len(partial)} 条\n\n")
        report_lines.append(f"| 英文术语 | 当前翻译 | 分类 | 来源 |\n")
        report_lines.append(f"|---------|---------|------|------|\n")
        for iss in partial[:50]:
            report_lines.append(f"| {iss['term']} | {iss['current_zh']} | {iss['category']} | {iss['source']} |\n")
        if len(partial) > 50:
            report_lines.append(f"| ... 另有 {len(partial)-50} 条 | 详见完整数据文件 | | |\n")

    report_lines.append(f"\n---\n")

    # Medium issues - deviations only (type=terminology_deviation)
    deviations = [iss for iss in by_severity.get("medium", []) if iss["type"] == "terminology_deviation"]
    if deviations:
        report_lines.append(f"## ⚠️ 术语偏差 (MEDIUM) — 翻译与权威标准不一致\n\n")
        report_lines.append(f"共 {len(deviations)} 条\n\n")
        report_lines.append(f"| 英文术语 | 当前翻译 | 标准翻译 | 权威来源 |\n")
        report_lines.append(f"|---------|---------|---------|--------|\n")
        for iss in deviations:
            report_lines.append(f"| {iss['term']} | {iss['current_zh']} | {iss['standard_zh']} | {iss['source']} |\n")

    report_lines.append(f"\n---\n")

    # Extras summary
    es = results["extras_summary"]
    report_lines.append(f"## 📋 额外术语 (extracted_extras) 处理建议\n\n")
    report_lines.append(f"共 {es['total']} 条，其中 {es['bad_zh']} 条翻译不合格\n\n")
    report_lines.append(f"来源分布:\n")
    report_lines.append(f"| 来源 | 数量 |\n")
    report_lines.append(f"|------|------|\n")
    for src, n in sorted(es["source_distribution"].items(), key=lambda x: -x[1]):
        report_lines.append(f"| {src} | {n} |\n")

    # Category coverage
    report_lines.append(f"\n## 📊 各分类术语质量\n\n")
    report_lines.append(f"| 分类 | ✅ 已验证 | ❓ 需审核 | ⚠️ 偏差 | ⚠️ 部分译 | 🚫 未译 |\n")
    report_lines.append(f"|------|----------|----------|---------|----------|--------|\n")
    for cat, qmap in sorted(results["category_quality"].items()):
        v = qmap.get("verified", 0)
        s = qmap.get("suspicious", 0)
        d = qmap.get("minor_deviation", 0)
        p = qmap.get("partial_translation", 0)
        g = qmap.get("garbage", 0)
        report_lines.append(f"| {cat} | {v} | {s} | {d} | {p} | {g} |\n")

    # Deviations detail (full list for action)
    if deviations:
        report_lines.append(f"\n## 📝 详细术语偏差清单（供逐个修正）\n\n")
        report_lines.append(f"| # | 英文 | 当前中文 | 标准中文 | 参考来源 |\n")
        report_lines.append(f"|---|------|---------|---------|--------|\n")
        for i, iss in enumerate(deviations, 1):
            report_lines.append(f"| {i} | {iss['term']} | {iss['current_zh']} | {iss['standard_zh']} | {iss['source']} |\n")

    # Suspicious terms (unverified_term type, high confidence)
    unverified = [iss for iss in by_severity.get("medium", []) if iss["type"] == "unverified_term"]
    if unverified:
        report_lines.append(f"\n## ❓ 未验证术语清单（需人工审核）\n\n")
        report_lines.append(f"| # | 英文 | 当前中文 | 来源 |\n")
        report_lines.append(f"|---|------|---------|------|\n")
        for i, iss in enumerate(unverified[:100], 1):
            report_lines.append(f"| {i} | {iss['term']} | {iss['current_zh']} | {iss['source']} |\n")

    return "".join(report_lines)


if __name__ == "__main__":
    results = analyze_v4_terms()

    if not results:
        sys.exit(1)

    # Save detailed JSON report
    report_file = KB / "terminology-verification-report.json"
    report_file.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\n✅ 详细报告: {report_file}", file=sys.stderr)

    # Generate and save issue list
    issue_md = generate_issue_list(results)
    issue_file = KB / "terminology-issue-list.md"
    issue_file.write_text(issue_md)
    print(f"  问题清单: {issue_file}", file=sys.stderr)

    # Print summary
    qs = results["stats"]["term_quality"]
    total = sum(qs.values())
    print(f"\n=== 术语翻译校审摘要 ===", file=sys.stderr)
    print(f"参考词典: {results['meta']['reference_dict_size']} 条", file=sys.stderr)
    print(f"总术语数: {total} (+ {results['meta']['total_extras']} extras)", file=sys.stderr)
    for q in ["verified", "suspicious", "minor_deviation", "partial_translation", "garbage"]:
        n = qs.get(q, 0)
        if n == 0:
            continue
        pct = n / total * 100
        label = {"verified": "已验证", "suspicious": "需审核",
                 "minor_deviation": "术语偏差",
                 "partial_translation": "部分翻译",
                 "garbage": "未翻译(仅英文)"}.get(q, q)
        print(f"  {label}: {n} ({pct:.1f}%)", file=sys.stderr)
    print(f"问题总数: {len(results['issues'])}", file=sys.stderr)
    print(f"Extras 不合格: {results['extras_summary']['bad_zh']}/{results['extras_summary']['total']}", file=sys.stderr)
