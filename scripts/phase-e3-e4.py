#!/usr/bin/env python3
"""Phase E3+E4: 审核可疑翻译 + 补齐部分翻译术语

Pipeline:
  1. 加载 v5 术语表
  2. E3: 审核疑似翻译 (50 条含英文缩写 + 1 条可疑)
  3. E4a: 修复 91 条中英混合翻译 (chilled水 → 冷冻水)
  4. E4b: 翻译 1317 条纯英文术语
  5. 输出 v6 术语表

用法: python3 scripts/phase-e3-e4.py
"""
import json, re, sys
from pathlib import Path
from collections import defaultdict, Counter
from datetime import date

BASE = Path(__file__).parent.parent
KB = BASE / "knowledge-base"

def load_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_bytes())

def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

# ── Known Chinese acronyms that should stay in zh ──
# These are English abbreviations/acronyms commonly used in Chinese mechanical eng
KNOWN_ACRONYMS = {
    "3d", "cad", "cam", "cae", "capp", "pdm", "plm", "erp", "mrp", "cims",
    "cnc", "nc", "dnc", "fms", "cmm", "plc", "pid", "hmi", "scada", "dcs",
    "led", "lcd", "ccd", "cmos", "ccd", "abs", "esp", "tcs", "ecu", "ecu",
    "fea", "fem", "cfd", "fem", "dem", "mbs", "mps", "mrp",
    "iso", "gb", "ansi", "din", "jis", "api", "asme", "astm", "sae", "iec",
    "pwm", "vfd", "ac", "dc", "rpm", "hp", "kw", "hz",
    "mig", "tig", "mag", "cswip", "ndt", "nde",
    "ppm", "tpm", "tqm", "qfd", "fmea", "spc", "oop", "oop",
    "vdi", "v-belt", "oring", "o-ring",
}

def has_chinese(s):
    return bool(re.search(r'[一-鿿]', s))

# ── Word-level map expansion for E4 ──
E4_WORD_MAP = {
    # Process verbs
    "recycling": "回收",
    "purification": "净化",
    "separation": "分离",
    "filtration": "过滤",
    "drying": "干燥",
    "mixing": "混合",
    "stirring": "搅拌",
    "agitation": "搅拌",
    "compaction": "压实",
    "sintering": "烧结",
    "hardfacing": "堆焊",
    "cladding": "覆层",
    "brazing": "钎焊",
    "soldering": "软钎焊",
    "riveting": "铆接",
    "threading": "攻丝",
    "tapping": "攻丝",
    "reaming": "铰孔",
    "boring": "镗孔",
    "broaching": "拉削",
    "planing": "刨削",
    "shaping": "插削",
    "sawing": "锯切",
    "lapping": "研磨",
    "honing": "珩磨",
    "superfinishing": "超精加工",
    "deburring": "去毛刺",
    "sandblasting": "喷砂",
    "shot peening": "喷丸",
    "pickling": "酸洗",
    "passivation": "钝化",
    "galvanizing": "镀锌",
    "anodizing": "阳极氧化",
    "electroplating": "电镀",
    "vacuum": "真空",
    "centrifugal": "离心",
    "reciprocating": "往复",
    "rotary": "旋转",
    "linear": "直线",
    "axial": "轴向",
    "radial": "径向",
    "tangential": "切向",
    "longitudinal": "纵向",
    "transverse": "横向",
    "vertical": "垂直",
    "horizontal": "水平",
    "parallel": "平行",
    "perpendicular": "垂直",
    "concentric": "同心",
    "eccentric": "偏心",
    "synchronous": "同步",
    "asynchronous": "异步",
    "variable": "可变",
    "constant": "恒定",
    "continuous": "连续",
    "intermittent": "间歇",
    "periodic": "周期",
    "random": "随机",
    "dynamic": "动态",
    "static": "静态",
    "elastic": "弹性",
    "plastic": "塑性",
    "viscoelastic": "黏弹性",
    "brittle": "脆性",
    "ductile": "延性",
    "malleable": "可锻",
    "porous": "多孔",
    "dense": "致密",
    "homogeneous": "均匀",
    "heterogeneous": "非均匀",
    "isotropic": "各向同性",
    "anisotropic": "各向异性",
    "transparent": "透明",
    "opaque": "不透明",

    # Nouns - tools & equipment
    "crane": "起重机",
    "hoist": "葫芦",
    "elevator": "升降机",
    "conveyor": "输送机",
    "elevator": "提升机",
    "compressor": "压缩机",
    "turbine": "涡轮机",
    "generator": "发电机",
    "transformer": "变压器",
    "boiler": "锅炉",
    "heater": "加热器",
    "cooler": "冷却器",
    "condenser": "冷凝器",
    "evaporator": "蒸发器",
    "radiator": "散热器",
    "exchanger": "换热器",
    "dryer": "干燥器",
    "filter": "过滤器",
    "separator": "分离器",
    "classifier": "分级机",
    "crusher": "破碎机",
    "mill": "磨机",
    "mixer": "混合机",
    "agitator": "搅拌器",
    "converter": "转炉",
    "reactor": "反应器",
    "column": "塔",
    "tower": "塔",
    "vessel": "容器",
    "tank": "罐",
    "bin": "料仓",
    "hopper": "料斗",
    "chute": "溜槽",
    "nozzle": "喷嘴",
    "orifice": "孔板",
    "diffuser": "扩压器",
    "impeller": "叶轮",
    "propeller": "螺旋桨",
    "rotor": "转子",
    "stator": "定子",
    "armature": "电枢",
    "commutator": "换向器",
    "brush": "电刷",
    "winding": "绕组",
    "coil": "线圈",
    "magnet": "磁铁",
    "solenoid": "螺线管",
    "actuator": "执行器",
    "transducer": "传感器",
    "thermocouple": "热电偶",
    "pyrometer": "高温计",
    "manometer": "压力计",
    "flowmeter": "流量计",
    "tachometer": "转速计",
    "dynamometer": "测功机",
    "strain gauge": "应变片",
    "extensometer": "引伸计",
    "caliper": "卡尺",
    "micrometer": "千分尺",
    "vernier": "游标",
    "protractor": "量角器",
    "compass": "圆规",
    "divider": "分规",
    "scriber": "划针",
    "hammer": "锤",
    "mallet": "木槌",
    "chisel": "凿",
    "file": "锉",
    "rasp": "粗锉",
    "drill": "钻",
    "reamer": "铰刀",
    "tap": "丝锥",
    "die": "板牙",
    "cutter": "刀具",
    "blade": "刀片",
    "bit": "钻头",
    "broach": "拉刀",
    "hob": "滚刀",
    "shaper cutter": "插齿刀",
    "grinding wheel": "砂轮",
    "abrasive": "磨料",
    "lapping compound": "研磨膏",
    "coolant": "切削液",
    "lubricant": "润滑剂",
    "grease": "润滑脂",
    "oil": "油",
    "emulsion": "乳化液",

    # Nouns - materials & properties
    "alloy": "合金",
    "superalloy": "高温合金",
    "composite": "复合材料",
    "laminate": "层压材料",
    "fiber": "纤维",
    "fiberglass": "玻璃纤维",
    "carbon fiber": "碳纤维",
    "kevlar": "凯夫拉",
    "nylon": "尼龙",
    "teflon": "聚四氟乙烯",
    "polyethylene": "聚乙烯",
    "polypropylene": "聚丙烯",
    "polycarbonate": "聚碳酸酯",
    "acrylic": "丙烯酸",
    "epoxy": "环氧",
    "polyurethane": "聚氨酯",
    "silicone": "硅胶",
    "elastomer": "弹性体",
    "thermoplastic": "热塑性",
    "thermoset": "热固性",
    "density": "密度",
    "porosity": "孔隙率",
    "permeability": "渗透率",
    "conductivity": "导电率",
    "resistivity": "电阻率",
    "permittivity": "介电常数",
    "viscosity": "黏度",
    "elasticity": "弹性",
    "plasticity": "塑性",
    "creep": "蠕变",
    "relaxation": "松弛",
    "hysteresis": "滞后",

    # Nouns - mechanisms & features
    "linkage": "连杆机构",
    "mechanism": "机构",
    "actuator": "执行机构",
    "transmission": "传动",
    "drivetrain": "传动系统",
    "gearbox": "齿轮箱",
    "differential": "差速器",
    "reducer": "减速器",
    "multiplier": "增速器",
    "governor": "调速器",
    "damper": "阻尼器",
    "shock absorber": "减振器",
    "isolator": "隔振器",
    "silencer": "消声器",
    "muffler": "消声器",
    "accumulator": "蓄能器",
    "intensifier": "增压器",
    "manifold": "歧管",
    "header": "集管",
    "baffle": "挡板",
    "partition": "隔板",
    "diaphragm": "膜片",
    "bellows": "波纹管",
    "gasket": "垫片",
    "packing": "填料",
    "lining": "衬里",
    "bushing": "衬套",
    "sleeve": "套筒",
    "guide": "导向",
    "rail": "导轨",
    "track": "轨道",
    "slide": "滑板",
    "ways": "导轨",
    "dovetail": "燕尾",
    "taper": "锥度",
    "chamfer": "倒角",
    "fillet": "圆角",
    "undercut": "退刀槽",
    "relief": "卸荷槽",
    "groove": "槽",
    "slot": "槽",
    "keyway": "键槽",
    "spline": "花键",
    "serration": "细齿",
    "knurling": "滚花",
    "counterbore": "沉孔",
    "countersink": "锥孔",
    "spotface": "凸台",
    "boss": "凸台",
    "lug": "凸耳",
    "tab": "凸片",
    "notch": "缺口",
    "indentation": "压痕",
    "dimple": "凹坑",
    "recess": "凹槽",
    "pocket": "凹腔",
    "cavity": "型腔",
    "core": "型芯",
    "insert": "嵌件",
    "liner": "衬板",
    "wear plate": "耐磨板",
    "stripper": "脱料板",
    "ejector": "顶出器",
    "knockout": "脱模",
    "sprue": "浇口",
    "runner": "流道",
    "gate": "浇口",
    "riser": "冒口",
    "vent": "排气孔",
    "dowel": "定位销",
    "locating pin": "定位销",
    "alignment pin": "对准销",
    "stop pin": "止动销",
    "retaining ring": "挡圈",
    "circlip": "卡簧",
    "snap ring": "卡环",

    # Nouns - technical concepts
    "principle": "原理",
    "hypothesis": "假设",
    "theory": "理论",
    "law": "定律",
    "rule": "规则",
    "axiom": "公理",
    "theorem": "定理",
    "corollary": "推论",
    "proof": "证明",
    "equation": "方程",
    "formula": "公式",
    "expression": "表达式",
    "function": "函数",
    "parameter": "参数",
    "variable": "变量",
    "constant": "常量",
    "coefficient": "系数",
    "modulus": "模量",
    "index": "指数",
    "exponent": "幂",
    "logarithm": "对数",
    "derivative": "导数",
    "integral": "积分",
    "gradient": "梯度",
    "divergence": "散度",
    "curl": "旋度",
    "laplacian": "拉普拉斯算子",
    "algorithm": "算法",
    "heuristic": "启发式",
    "optimization": "优化",
    "simulation": "仿真",
    "iteration": "迭代",
    "convergence": "收敛",
    "stability": "稳定性",
    "reliability": "可靠性",
    "availability": "可用性",
    "maintainability": "可维修性",
    "durability": "耐久性",
    "service life": "使用寿命",
    "shelf life": "保质期",
    "lead time": "提前期",
    "cycle time": "周期",
    "downtime": "停机时间",
    "uptime": "运行时间",
    "throughput": "吞吐量",
    "capacity": "容量",
    "capability": "能力",
    "performance": "性能",
    "efficiency": "效率",
    "productivity": "生产率",
    "quality": "质量",
    "precision": "精度",
    "accuracy": "准确度",
    "resolution": "分辨率",
    "sensitivity": "灵敏度",
    "specificity": "特异性",
    "tolerance": "公差",
    "allowance": "余量",
    "clearance": "间隙",
    "interference": "过盈",
    "shrinkage": "收缩",
    "expansion": "膨胀",
    "distortion": "变形",
    "warpage": "翘曲",
    "deflection": "挠度",
    "buckling": "屈曲",

    # Etymology/prefixes
    "bio": "生物",
    "eco": "生态",
    "geo": "地质",
    "hydro": "水",
    "aero": "空气",
    "thermo": "热",
    "electro": "电",
    "magneto": "磁",
    "opto": "光",
    "acousto": "声",
    "piezo": "压电",
    "tribo": "摩擦",
    "chemo": "化学",
    "mechano": "机械",
    "chrono": "时间",
    "servo": "伺服",
    "hydrostatic": "静压",
    "hydrodynamic": "动压",
    "aerodynamic": "气动",
    "thermodynamic": "热力",
    "electromagnetic": "电磁",
    "electromechanical": "机电",
    "mechatronic": "机电一体化",
    "optoelectronic": "光电",
    "thermoelectric": "热电",
    "photovoltaic": "光伏",

    # Additional common roots
    "analysis": "分析",
    "synthesis": "合成",
    "diagnosis": "诊断",
    "dynamics": "动力学",
    "kinematics": "运动学",
    "kinetics": "动力学",
    "statics": "静力学",
    "mechanics": "力学",
    "thermodynamics": "热力学",
    "hydraulics": "液压技术",
    "pneumatics": "气动技术",
    "tribology": "摩擦学",
    "metrology": "计量学",
    "ergonomics": "人机工程学",

    # Processing adjectives
    "fused": "熔融",
    "molten": "熔融",
    "sintered": "烧结",
    "cast": "铸造",
    "forged": "锻造",
    "rolled": "轧制",
    "drawn": "拉拔",
    "extruded": "挤压",
    "machined": "机加工",
    "ground": "磨削",
    "polished": "抛光",
    "coated": "涂层",
    "plated": "电镀",
    "heat treated": "热处理",
    "cold worked": "冷加工",
    "hot worked": "热加工",
    "case hardened": "表面硬化",
    "induction hardened": "感应淬火",
    "flame hardened": "火焰淬火",
    "nitrided": "渗氮",
    "carburized": "渗碳",
    "galvanized": "镀锌",
    "anodized": "阳极氧化",
    "hard": "硬",
    "soft": "软",
    "tough": "韧",
    "brittle": "脆",
    "strong": "强",
    "weak": "弱",
    "rigid": "刚",
    "flexible": "柔",
    "stiff": "刚",
}

def compose_translation_v2(en_term, term_dict, word_dict, pattern_rules):
    """Enhanced translation composer that handles more complex patterns"""
    en_lower = en_term.strip().lower()

    # 1. Exact match
    if en_lower in term_dict:
        return term_dict[en_lower]

    # 2. Pattern rules (suffix-based)
    for pattern, template in pattern_rules:
        m = re.match(pattern, en_lower, re.IGNORECASE)
        if m:
            prefix = m.group(1)
            # Try to translate prefix (without recursion limit issues)
            prefix_zh = compose_translation_v2(prefix, term_dict, word_dict, pattern_rules)
            if prefix_zh:
                result = template.replace(r'\1', prefix_zh)
                return result

    # 3. Word-by-word composition
    words = en_lower.replace('-', ' ').replace('_', ' ').replace('/', ' ').split()
    if len(words) >= 2:
        zh_parts = []
        # Merge word_dict and E4_WORD_MAP
        combined_dict = {}
        combined_dict.update(word_dict)
        combined_dict.update(E4_WORD_MAP)

        for w in words:
            if w in combined_dict:
                zh_parts.append(combined_dict[w])
            elif w in KNOWN_ACRONYMS:
                zh_parts.append(w.upper())
            else:
                # Try the word itself as a term
                sub_result = compose_translation_v2(w, term_dict, combined_dict, pattern_rules)
                if sub_result:
                    zh_parts.append(sub_result)
                else:
                    # Try stripping trailing 's' (plural)
                    if w.endswith('s') and len(w) > 3:
                        singular = w[:-1]
                        if singular in combined_dict:
                            zh_parts.append(combined_dict[singular])
                        elif singular in KNOWN_ACRONYMS:
                            zh_parts.append(singular.upper())
                        else:
                            return None
                    else:
                        return None

        if zh_parts:
            return ''.join(zh_parts)

    # 4. Single word + E4_WORD_MAP
    if len(words) == 1:
        combined_dict = dict(word_dict)
        combined_dict.update(E4_WORD_MAP)
        if words[0] in combined_dict:
            return combined_dict[words[0]]
        # Handle plural
        if words[0].endswith('s') and len(words[0]) > 3:
            singular = words[0][:-1]
            if singular in combined_dict:
                return combined_dict[singular]

    return None


def phase_e3_review_acronyms(v5_terms, term_dict):
    """Phase E3: Review terms with embedded acronyms (50 terms)

    Classifies each as:
      - verified: correct as-is (e.g. PID控制, 3D打印)
      - fixed: needs correction
    """
    results = {"verified": [], "fixed": [], "unclear": []}
    for t in v5_terms:
        zh = t.get("zh", "")
        en = t.get("en", "")
        if not re.search(r'[a-zA-Z]', zh):
            continue
        if not has_chinese(zh):
            continue

        # Check if this is an acronym term
        has_acronym = False
        for acr in KNOWN_ACRONYMS:
            if acr.upper() in en.upper():
                has_acronym = True
                break
        if not has_acronym:
            continue

        # Check the translation quality
        zh_has_en_alpha = bool(re.search(r'[A-Za-z]', zh))
        zh_has_cn = has_chinese(zh)

        if zh_has_en_alpha and zh_has_cn:
            # Has both - likely correct (e.g., PID控制, V带)
            # Try to verify: check if the en contains known acronym
            acronyms_found = []
            for acr in KNOWN_ACRONYMS:
                pattern = r'\b' + re.escape(acr) + r'\b'
                if re.search(pattern, en, re.IGNORECASE):
                    acronyms_found.append(acr.upper())

            has_meaningful_acronym = len(acronyms_found) > 0

            if has_meaningful_acronym:
                t["translation_quality"] = "verified"
                t["review_note"] = f"E3: 缩写词 {','.join(acronyms_found)} 保持英文"
                results["verified"].append(t)
            else:
                results["unclear"].append(t)

    return results


def phase_e3_review_suspicious(v5_terms, term_dict):
    """Phase E3: Check any remaining suspicious terms"""
    # Find terms where zh == en (case-insensitive) - these are completely untranslated
    suspicious = []
    for t in v5_terms:
        zh = t.get("zh", "")
        en = t.get("en", "")
        if not zh or zh.strip().lower() == en.strip().lower():
            suspicious.append(t)
    return suspicious


def phase_e4_fix_bad_mixed(v5_terms, term_dict, word_dict, pattern_rules, e4_word_map):
    """Phase E4a: Fix 91 badly-mixed translations"""
    fixed_count = 0
    fixed_terms = []

    # Build combined word dictionary
    combined = {}
    combined.update(word_dict)
    combined.update(e4_word_map)

    for t in v5_terms:
        zh = t.get("zh", "")
        en = t.get("en", "")
        if not has_chinese(zh):
            continue  # Skip pure English (handled by E4b)

        # Check if zh has lowercased English words (the 'bad mixing' pattern)
        # Pattern: "chilled水" or "circulating水plant" - where an English word is left untranslated
        # and placed before/after Chinese characters

        # Find English words in zh that should be translated
        en_words_in_zh = re.findall(r'\b[a-zA-Z]+\b', zh)
        needs_fix = False
        for ew in en_words_in_zh:
            ew_lower = ew.lower()
            if ew_lower in combined:
                needs_fix = True
                break
            if ew_lower in KNOWN_ACRONYMS:
                continue

        if not needs_fix:
            continue

        # Re-translate using the enhanced composer
        result = compose_translation_v2(en, term_dict, combined, pattern_rules)
        if result:
            t["zh"] = result
            t["source"] = t.get("source", "") + "+e4"
            t["translation_quality"] = "e4_fixed"
            fixed_count += 1
            fixed_terms.append((en, zh, result))
        else:
            # Manual fix for common patterns
            # Word-by-word replacement
            new_zh = zh
            for ew in sorted(en_words_in_zh, key=len, reverse=True):
                ew_lower = ew.lower()
                if ew_lower in combined and ew_lower not in KNOWN_ACRONYMS:
                    new_zh = new_zh.replace(ew, combined[ew_lower], 1)

            if new_zh != zh:
                t["zh"] = new_zh
                t["source"] = t.get("source", "") + "+e4"
                t["translation_quality"] = "e4_fixed"
                fixed_count += 1
                fixed_terms.append((en, zh, new_zh))

    return fixed_count, fixed_terms


def phase_e4_translate_pure_en(v5_terms, term_dict, word_dict, pattern_rules, e4_word_map):
    """Phase E4b: Translate 1317 pure English terms"""
    fixed_count = 0
    fixed_terms = []
    failed = []

    combined = {}
    combined.update(word_dict)
    combined.update(e4_word_map)

    for t in v5_terms:
        zh = t.get("zh", "")
        en = t.get("en", "")

        # Only process terms with no Chinese at all
        if has_chinese(zh):
            continue

        # Check if it's a pure English copy (untranslated)
        if not zh or zh.strip().lower() == en.strip().lower():
            # Try to translate
            result = compose_translation_v2(en, term_dict, combined, pattern_rules)
            if result:
                t["zh"] = result
                t["source"] = t.get("source", "") + "+e4b"
                t["translation_quality"] = "e4b_translated"
                fixed_count += 1
                fixed_terms.append((en, zh, result))
            else:
                failed.append(en)

    return fixed_count, fixed_terms, failed


def phase_e4_translate_extras(v5_extras, term_dict, word_dict, pattern_rules, e4_word_map):
    """Also fix extracted_extras that are untranslated"""
    fixed_count = 0
    fixed_extras = []

    combined = {}
    combined.update(word_dict)
    combined.update(e4_word_map)

    for e in v5_extras:
        zh = e.get("zh", "")
        en = e.get("en", "")

        if has_chinese(zh):
            continue
        if not zh or zh.strip().lower() == en.strip().lower():
            result = compose_translation_v2(en, term_dict, combined, pattern_rules)
            if result:
                e["zh"] = result
                e["source"] = e.get("source", "") + "+e4b"
                fixed_count += 1
                fixed_extras.append((en, zh, result))

    return fixed_count, fixed_extras



def classify_failed_terms(terms):
    """Classify untranslated terms into categories for better handling"""
    import re

    person_name_pattern = re.compile(
        r'^(Dr\.?\s+|Professor\s+|Sir\s+|Saint\s+)?'
        r'([A-Z][a-zéèêëàâäùûüôöîïçÉÈÊËÀÂÄÙÛÜÔÖÎÏÇ]+'
        r'(\s+[A-Z][a-zéèêëàâäùûüôöîïçÉÈÊËÀÂÄÙÛÜÔÖÎÏÇ.]+){1,4})$'
    )
    org_pattern = re.compile(
        r'(University|Institute|College|School|Association|Society|'
        r'Laboratory|Centre|Center|Foundation|Council|Commission|'
        r'Committee|Organization|Company|Corporation|Inc\.|Ltd\.|'
        r'International|Standard|Engineers|Handbook|Engineering)$'
    )
    pub_pattern = re.compile(
        r'(Journal|Magazine|Bulletin|Report|Code|Standard|Manual|'
        r'Guide|Handbook|Proceedings|Transactions|Review|Letter)$'
    )
    proper_noun_pattern = re.compile(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)+$')
    acronym_pattern = re.compile(r'^[A-Z]{2,}$')

    categories = {
        "person_name": [],
        "organization": [],
        "publication": [],
        "proper_noun": [],
        "acronym": [],
        "generic_term": [],
        "specialized_term": [],
    }

    for t in terms:
        en = t.get('en', '') if isinstance(t, dict) else t
        if not en:
            continue
        en_stripped = en.strip()

        # Acronym
        if acronym_pattern.match(en_stripped) and len(en_stripped) >= 2:
            categories["acronym"].append(en)
            continue

        # Person name (multi-word, all capitalized words, 3+ letters each)
        if person_name_pattern.match(en_stripped):
            words = en_stripped.split()
            if len(words) >= 2 and all(w[0].isupper() for w in words if w not in {'of', 'the', 'and', 'for', 'in', 'de', 'van', 'von'}):
                categories["person_name"].append(en)
                continue

        # Organization
        if org_pattern.search(en_stripped):
            categories["organization"].append(en)
            continue

        # Publication
        if pub_pattern.search(en_stripped):
            categories["publication"].append(en)
            continue

        # Multi-word proper noun (each word capitalized)
        if proper_noun_pattern.match(en_stripped):
            words = en_stripped.split()
            if len(words) >= 3:
                categories["proper_noun"].append(en)
                continue

        # Generic term (starts lowercase or mixed)
        if en_stripped[0].islower():
            categories["generic_term"].append(en)
            continue

        # Default: specialized term
        categories["specialized_term"].append(en)

    return categories


def phase_e4_v2_generic_translate(terms, term_dict, word_dict, pattern_rules, e4_word_map):
    """Phase E4 v2: Translate generic terms using expanded strategies"""
    import re

    fixed = []
    combined = {}
    combined.update(word_dict)
    combined.update(e4_word_map)

    # Additional suffix patterns not in original
    extra_patterns = [
        (r'^(.+)\s+properties$', r'\1性能'),
        (r'^(.+)\s+characteristics$', r'\1特性'),
        (r'^(.+)\s+behavior$', r'\1行为'),
        (r'^(.+)\s+response$', r'\1响应'),
        (r'^(.+)\s+design$', r'\1设计'),
        (r'^(.+)\s+analysis$', r'\1分析'),
        (r'^(.+)\s+model$', r'\1模型'),
        (r'^(.+)\s+data$', r'\1数据'),
        (r'^(.+)\s+information$', r'\1信息'),
        (r'^(.+)\s+pattern$', r'\1模式'),
        (r'^(.+)\s+effect$', r'\1效应'),
        (r'^(.+)\s+condition$', r'\1条件'),
        (r'^(.+)\s+calculation$', r'\1计算'),
        (r'^(.+)\s+materials$', r'\1材料'),
        (r'^(.+)\s+production$', r'\1生产'),
        (r'^(.+)\s+management$', r'\1管理'),
        (r'^(.+)\s+testing$', r'\1试验'),
        (r'^(.+)\s+applications$', r'\1应用'),
        (r'^(.+)\s+standards$', r'\1标准'),
        (r'^(.+)\s+source$', r'\1源'),
        (r'^(.+)\s+technique$', r'\1技术'),
        (r'^(.+)\s+practice$', r'\1实践'),
    ]

    all_patterns = list(pattern_rules) + extra_patterns

    for term_en in terms:
        en_lower = term_en.strip().lower()

        # 1. Try exact match
        if en_lower in term_dict:
            fixed.append((term_en, term_dict[en_lower]))
            continue

        # 2. Try pattern rules (with fix for backslash)
        found = False
        for pattern, template in all_patterns:
            m = re.match(pattern, en_lower, re.IGNORECASE)
            if m:
                prefix = m.group(1)
                # Try translate prefix with simple word-map
                words = prefix.replace('-', ' ').split()
                zh_parts = []
                all_ok = True
                for w in words:
                    if w in combined:
                        zh_parts.append(combined[w])
                    elif w in KNOWN_ACRONYMS:
                        zh_parts.append(w.upper())
                    elif len(words) == 1:
                        all_ok = False
                        break
                    else:
                        all_ok = False
                        break
                if all_ok:
                    result = ''.join(zh_parts) + template.split('\1')[1] if '\1' in template else template
                    # Simpler: just append suffix
                    if template.startswith(r'\1'):
                        suffix = template[2:]
                        result = ''.join(zh_parts) + suffix
                        fixed.append((term_en, result))
                        found = True
                        break

        if found:
            continue

        # 3. Try word-by-word composition
        words = en_lower.replace('-', ' ').replace("'", ' ').split()
        zh_parts = []
        all_found = True
        for w in words:
            if w in combined:
                zh_parts.append(combined[w])
            elif w in KNOWN_ACRONYMS:
                zh_parts.append(w.upper())
            else:
                all_found = False
                break

        if all_found and zh_parts:
            fixed.append((term_en, ''.join(zh_parts)))
            found = True

    return fixed

def main():
    print("=" * 60)
    print("Phase E3+E4: 可疑翻译审核 + 部分翻译补齐")
    print(f"日期: {date.today().isoformat()}")
    print("=" * 60)

    # Load v5
    v5 = load_json(KB / "mech-terminology-v5.json")
    if not v5:
        print("ERROR: mech-terminology-v5.json not found", file=sys.stderr)
        sys.exit(1)

    terms = v5.get("terms", [])
    extras = v5.get("extracted_extras", [])
    print(f"\n加载 v5: {len(terms)} terms, {len(extras)} extras")

    # Load translation engine from phase-e1-e2
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("phase_e1_e2",
                                                       BASE / "scripts" / "phase-e1-e2.py")
        e1e2_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(e1e2_mod)
        _term_dict, _word_dict, _pattern_rules = e1e2_mod.build_translation_engine()
        print(f"翻译引擎: {len(_term_dict)} 精确匹配, {len(_word_dict)} 词级映射, {len(_pattern_rules)} 模式规则")
    except Exception as e:
        print(f"WARNING: Cannot import phase-e1-e2 ({e}), using embedded fallback")
        _term_dict, _word_dict, _pattern_rules = {}, {}, []

    # ── Phase E3: Review ──
    print("\n── Phase E3: 审核可疑翻译 ──")

    # E3a: Review acronym terms (50)
    e3a_results = phase_e3_review_acronyms(terms, _term_dict)
    print(f"  ✓ 缩写词已确认: {len(e3a_results['verified'])}")
    print(f"  ? 缩写词待确认: {len(e3a_results['unclear'])}")
    if e3a_results['unclear']:
        for t in e3a_results['unclear'][:10]:
            print(f"    {t['en']:50s} → {t['zh']}")

    # E3b: Check suspicious (untranslated/lowercased)
    e3b_suspicious = phase_e3_review_suspicious(terms, _term_dict)
    print(f"  ✗ 未翻译术语: {len(e3b_suspicious)}")

    # Search for quality issues
    quality_issues = []
    for t in terms:
        zh = t.get("zh", "")
        en = t.get("en", "")
        if not zh:
            quality_issues.append(t)
        elif zh == en.lower().strip():
            quality_issues.append(t)
        elif "是机械工程领域的重要概念" in zh:
            quality_issues.append(t)

    print(f"  ✗ 质量缺陷: {len(quality_issues)}")

    # ── Phase E4a: Fix bad-mixed ──
    print("\n── Phase E4a: 修复中英混合翻译 ──")
    e4a_count, e4a_terms = phase_e4_fix_bad_mixed(terms, _term_dict, _word_dict, _pattern_rules, E4_WORD_MAP)
    print(f"  ✓ 已修复: {e4a_count}")
    if e4a_terms:
        for en, old, new in e4a_terms[:10]:
            print(f"    {en:50s} '{old:20s}' → '{new}'")

    # ── Phase E4b: Translate pure English ──
    print("\n── Phase E4b: 翻译纯英文术语 ──")
    e4b_count, e4b_terms, e4b_failed = phase_e4_translate_pure_en(terms, _term_dict, _word_dict, _pattern_rules, E4_WORD_MAP)
    print(f"  ✓ 已翻译: {e4b_count}")
    if e4b_terms:
        for en, old, new in e4b_terms[:10]:
            print(f"    {en:50s} → {new}")
    if e4b_failed:
        print(f"  ✗ 翻译失败: {len(e4b_failed)}")
        for en in e4b_failed[:20]:
            print(f"    {en}")

    # ── E4b extras ──
    print("\n── E4b extras: 翻译额外术语 ──")
    e4b_ex_count, e4b_ex_terms = phase_e4_translate_extras(extras, _term_dict, _word_dict, _pattern_rules, E4_WORD_MAP)
    print(f"  ✓ 已翻译: {e4b_ex_count}")

    # ── Final stats ──
    print("\n" + "=" * 60)
    print("最终统计")
    print("=" * 60)

    # Recalculate quality
    verified_count = sum(1 for t in terms
                         if not re.search(r'[a-zA-Z]', t.get("zh", ""))
                         and has_chinese(t.get("zh", "")))
    partial_count = sum(1 for t in terms
                        if re.search(r'[a-zA-Z]', t.get("zh", ""))
                        and has_chinese(t.get("zh", "")))
    pure_en_count = sum(1 for t in terms
                        if not has_chinese(t.get("zh", "")))
    empty_count = sum(1 for t in terms if not t.get("zh", ""))

    print(f"  Total terms: {len(terms)}")
    print(f"  ✓ 合格中文翻译: {verified_count}")
    print(f"  ! 中英混合: {partial_count}")
    print(f"  ✗ 纯英文: {pure_en_count}")
    print(f"  ✗ 空: {empty_count}")

    # Save v6
    v5["meta"]["version"] = "6"
    v5["meta"]["version_date"] = date.today().isoformat()
    v5["meta"]["phase_e3_verified_acronyms"] = len(e3a_results['verified'])
    v5["meta"]["phase_e4a_fixed_mixed"] = e4a_count
    v5["meta"]["phase_e4b_translated"] = e4b_count
    v5["meta"]["phase_e4b_extras_translated"] = e4b_ex_count
    v5["meta"]["phase_e4b_failed"] = len(e4b_failed)

    v6_path = KB / "mech-terminology-v6.json"
    save_json(v6_path, v5)
    print(f"\n✅ 已保存 v6: {v6_path}")

    # Save failed list for manual review
    if e4b_failed:
        failed_path = KB / "terminology-e4b-failed.json"
        save_json(failed_path, {"failed_terms": sorted(set(e4b_failed))})
        print(f"📋 失败清单: {failed_path}")

    return v5, v6_path


if __name__ == "__main__":
    main()
