#!/usr/bin/env python3
"""
Phase E4-v3: Batch translate 242 single mechanical engineering terms.
Applies standard Chinese translations to the remaining untranslated single terms.
"""
import json, re
from pathlib import Path

BASE = Path(__file__).parent.parent
KB = BASE / "knowledge-base"

# Standard Chinese translations for 242 single mechanical engineering terms
TRANSLATIONS = {
    # ── Wikipedia terms (general mechanical engineering) ──
    "Airflow": "气流",
    "Brinelling": "布氏压痕",
    "Bullwheel": "导向轮",
    "Burnishing": "滚光",
    "COMOS": "COMOS",  # proper noun - keeps English
    "Crumpling": "压溃",
    "Hemorheology": "血液流变学",
    "Dexel": "体素",
    "Duality": "对偶性",
    "Formability": "成形性",
    "Galling": "咬合",
    "Hütte": "胡特",  # German proper noun
    "Jib": "吊臂",
    "Kludge": "权宜方案",
    "Longeron": "纵梁",
    "MEMS": "微机电系统",
    "Metalworking": "金属加工",
    "Roadworthiness": "道路行驶适运性",
    "Superlubricity": "超润滑",
    "Swivel": "旋转接头",
    "Treadle": "踏板",
    "Turboexpander": "涡轮膨胀机",
    "Bating": "软化处理",
    "Bleachfield": "漂白场",
    "Skelp": "管坯",
    "Cloakmaker": "制斗匠",
    "Fordism": "福特制",
    "Marudai": "丸台",
    "Monozukuri": "造物",
    "Downstream": "下游",
    "Register": "风量调节器",

    # ── EngineersEdge (general/steel/standards) ──
    "Cold": "冷",
    "Ball": "球",
    "Spur": "直齿",
    "Selecting": "选择",
    "Fteley": "弗特利",
    "Selection": "选择",
    "AISI": "美国钢铁学会",
    "IPN": "IPN",  # standard profile designation
    "NEMA": "美国电气制造商协会",
    "Speeds": "速度",
    "Acoustics": "声学",
    "Hex": "六角",
    "100": "100",  # numeric - keep as-is
    "Hexagon": "六边形",
    "Metric": "公制",
    "Soils": "土壤",

    # ── Variant-v4 (heat treatment / surface engineering) ──
    "spheroidizing": "球化退火",
    "homogenizing": "均匀化退火",
    "patenting": "索氏体化处理",
    "chromizing": "渗铬",
    "aluminizing": "渗铝",
    "siliconizing": "渗硅",
    "varnishing": "浸漆",
    "lacquering": "喷漆",
    "enameling": "搪瓷",
    "hvof": "超音速火焰喷涂",
    "tumbling": "滚光",
    "etching": "蚀刻",
    "bluing": "发蓝",
    "fretting": "微动磨损",
    "spalling": "剥落",
    "delamination": "分层",
    "rupture": "断裂",
    "tearing": "撕裂",
    "galloseizing": "咬死",
    "overload": "过载",
    "elongation": "伸长率",
    "balance": "平衡",
    "stroboscope": "频闪仪",
    "anemometer": "风速计",
    "barometer": "气压计",
    "hygrometer": "湿度计",
    "thermometer": "温度计",
    "thermistor": "热敏电阻",
    "rotameter": "转子流量计",

    # ── Variant-v5 (standards/quality) ──
    "ieee": "电气电子工程师学会",
    "api": "美国石油学会",
    "ul": "美国保险商实验室",
    "ce": "CE认证",
    "bs": "英国标准",
    "gb": "国家标准",
    "en": "欧洲标准",
    "iec": "国际电工委员会",
    "nace": "美国腐蚀工程师协会",
    "kaizen": "改善",
    "kanban": "看板",
    "5s": "5S管理",
    "circularity": "圆度",
    "position": "位置度",
    "emissivity": "发射率",
    "absorptivity": "吸收率",
    "reflectivity": "反射率",
    "annubar": "阿牛巴流量计",
    "necking": "颈缩",

    # ── v6 HVAC ──
    "ductwork": "风管系统",
    "grille": "百叶窗",
    "humidifier": "加湿器",
    "dehumidifier": "除湿器",
    "psychrometrics": "湿空气学",
    "thermostat": "恒温器",

    # ── v6 Automotive ──
    "distributor": "分电器",
    "alternator": "交流发电机",
    "intercooler": "中间冷却器",
    "turbocharger": "涡轮增压器",
    "supercharger": "机械增压器",
    "lifter": "挺杆",
    "flywheel": "飞轮",
    "flexplate": "柔性板",
    "struts": "支柱",

    # ── v6 Plumbing ──
    "downpipe": "排水管",
    "gutter": "檐槽",
    "faucet": "水龙头",
    "spigot": "插口",
    "bibcock": "龙头",

    # ── v6 Construction ──
    "foundation": "基础",
    "footing": "基座",
    "caisson": "沉箱",
    "tieback": "锚杆",
    "beam": "梁",
    "girder": "主梁",
    "joist": "托梁",
    "purlin": "檩条",
    "truss": "桁架",
    "pillar": "柱",
    "pier": "桥墩",
    "abutment": "桥台",
    "rebar": "钢筋",
    "stirrup": "箍筋",
    "tie": "系杆",
    "formwork": "模板",
    "shoring": "支撑",
    "falsework": "脚手架",
    "centering": "拱架",
    "waterstop": "止水带",

    # ── v6 Power ──
    "superheater": "过热器",
    "reheater": "再热器",
    "economizer": "省煤器",
    "burner": "燃烧器",
    "windbox": "风箱",
    "ignitor": "点火器",
    "sootblower": "吹灰器",
    "baghouse": "袋式除尘器",
    "exciter": "励磁机",
    "switchyard": "开关站",
    "gis": "气体绝缘开关设备",
    "combustor": "燃烧室",

    # ── v6 Mining ──
    "hydrocyclone": "水力旋流器",
    "thickener": "浓缩机",
    "clarifier": "澄清器",
    "winders": "提升机",
    "sheave": "滑轮",
    "cage": "罐笼",
    "skip": "箕斗",
    "loader": "装载机",
    "scoop": "铲斗",
    "shovel": "挖掘机",
    "excavator": "挖掘机",
    "dozer": "推土机",
    "compactor": "压实机",
    "roller": "压路机",

    # ── v6 Marine ──
    "hull": "船体",
    "bulkhead": "舱壁",
    "deck": "甲板",
    "superstructure": "上层建筑",
    "forecastle": "艏楼",
    "bridge": "驾驶室",
    "rudder": "舵",
    "anchor": "锚",
    "windlass": "起锚机",
    "capstan": "绞盘",
    "bollard": "系缆桩",
    "fairlead": "导缆孔",
    "fender": "护舷",
    "stabilizer": "减摇装置",
    "lifeboat": "救生艇",
    "davit": "吊艇架",
    "gangway": "舷梯",
    "scuttle": "舱口",
    "porthole": "舷窗",
    "deadlight": "舷窗盖",
    "mast": "桅杆",
    "boom": "吊杆",
    "derrick": "井架",
    "cofferdam": "隔离舱",

    # ── v6 Manufacturing ──
    "pultrusion": "拉挤成型",

    # ── v6 Engineering (math) ──
    "calculus": "微积分",
    "matrix": "矩阵",
    "determinant": "行列式",
    "eigenvalue": "特征值",
    "eigenvector": "特征向量",
    "interpolation": "插值",
    "nurbs": "非均匀有理B样条",
    "statistics": "统计学",
    "probability": "概率论",

    # ── v6 Safety ──
    "goggles": "护目镜",
    "earplug": "耳塞",
    "earmuff": "耳罩",
    "lanyard": "安全绳",
    "interlock": "互锁",
    "standpipe": "竖管",

    # ── v6 Measuring ──
    "interferometer": "干涉仪",

    # ── v6 More ──
    "torx": "内梅花",

    # ── v6 Agricultural ──
    "cultivator": "中耕机",
    "plow": "犁",
    "harrow": "耙",
    "seeder": "播种机",
    "planter": "种植机",
    "baler": "打捆机",
    "mower": "割草机",
    "tedder": "摊晒机",
    "subsoiler": "深松机",
    "ripper": "松土机",
    "packer": "镇压器",
    "ditcher": "挖沟机",
    "trencher": "开沟机",
    "backhoe": "反铲挖掘机",
    "forklift": "叉车",
    "telehandler": "伸缩臂叉装车",
    "manlift": "升降平台",
    "silo": "筒仓",

    # ── v6 Railway ──
    "fishplate": "鱼尾板",
    "ballast": "道砟",
    "subballast": "底砟",
    "turnout": "道岔",
    "frog": "辙叉",
    "crossing": "交叉渡线",
    "bumper": "缓冲器",
    "milepost": "里程标",
    "locomotive": "机车",
    "boxcar": "棚车",
    "flatcar": "平车",
    "caboose": "守车",
    "streetcar": "有轨电车",
    "coupler": "车钩",
    "buffer": "缓冲器",
    "wheel": "车轮",
    "wheelset": "轮对",
    "bogie": "转向架",
    "truck": "转向架",
    "dampener": "阻尼器",
    "snubber": "减振器",
}


def main():
    print("=" * 60)
    print("Phase E4-v3: 批量翻译 242 个单术语")
    print("=" * 60)

    v8 = json.loads((KB / "mech-terminology-v8.json").read_bytes())
    terms = v8.get("terms", [])

    applied = 0
    already_zh = 0
    not_found = 0

    for t in terms:
        en = t.get("en", "").strip()
        zh = t.get("zh", "").strip()

        # Skip if already has Chinese
        if re.search(r'[一-鿿]', zh):
            already_zh += 1
            continue

        # Check if we have a translation
        if en in TRANSLATIONS:
            old_zh = zh if zh else "(empty)"
            t["zh"] = TRANSLATIONS[en]
            t["source"] = t.get("source", "") + "+e4v3"
            t["translation_quality"] = "e4v3"
            applied += 1
        else:
            # Also try case-insensitive
            en_lower = en.lower()
            for key, val in TRANSLATIONS.items():
                if key.lower() == en_lower:
                    t["zh"] = val
                    t["source"] = t.get("source", "") + "+e4v3"
                    t["translation_quality"] = "e4v3"
                    applied += 1
                    break
            else:
                not_found += 1

    print(f"\n✓ 已翻译: {applied}")
    print(f"- 原已有中文: {already_zh}")
    print(f"- 未找到映射: {not_found}")

    # Also handle the 89 mixed terms with a second pass
    mixed_fixed = 0
    mixed_remaining = 0
    for t in terms:
        zh = t.get("zh", "")
        en = t.get("en", "")
        if not re.search(r'[a-zA-Z]', zh) or not re.search(r'[一-鿿]', zh):
            continue
        # Try to fix remaining lowercase English words
        remaining_en = [w for w in re.findall(r'[a-z]+', zh) if len(w) >= 3]
        if remaining_en:
            # Check if these are in our TRANSLATIONS
            new_zh = zh
            for w in sorted(remaining_en, key=len, reverse=True):
                if w in TRANSLATIONS:
                    new_zh = new_zh.replace(w, TRANSLATIONS[w], 1)
                elif w.capitalize() in TRANSLATIONS:
                    new_zh = new_zh.replace(w, TRANSLATIONS[w.capitalize()], 1)

            remaining_after = [w for w in re.findall(r'[a-z]+', new_zh) if len(w) >= 2]
            if not remaining_after:
                t["zh"] = new_zh
                t["source"] = t.get("source", "") + "+e4v3"
                mixed_fixed += 1
            else:
                mixed_remaining += 1

    print(f"\n中英混合二次修复: {mixed_fixed}")
    print(f"混合未修复: {mixed_remaining}")

    # Final stats
    verified = sum(1 for t in terms
                   if not re.search(r'[a-zA-Z]', t.get("zh", ""))
                   and re.search(r'[一-鿿]', t.get("zh", "")))
    mixed = sum(1 for t in terms
                if re.search(r'[a-zA-Z]', t.get("zh", ""))
                and re.search(r'[一-鿿]', t.get("zh", "")))
    untranslated = sum(1 for t in terms
                       if not re.search(r'[一-鿿]', t.get("zh", "")))

    print(f"\n{'='*60}")
    print(f"最终 v9 统计")
    print(f"{'='*60}")
    print(f"  ✓ 合格中文: {verified}")
    print(f"  ⚠ 中英混合: {mixed}")
    print(f"  ✗ 纯英文: {untranslated}")
    print(f"  总计: {len(terms)}")

    # Save v9
    v8["meta"]["version"] = "9"
    v8["meta"]["version_date"] = "2026-05-18"
    v8["meta"]["phase_e4v3_single_terms"] = applied
    v8["meta"]["phase_e4v3_mixed_fixed"] = mixed_fixed
    v8["meta"]["verified_total"] = verified
    v8["meta"]["mixed_remaining"] = mixed
    v8["meta"]["untranslated_remaining"] = untranslated

    v9_path = KB / "mech-terminology-v9.json"
    v9_path.write_text(json.dumps(v8, ensure_ascii=False, indent=2))
    print(f"\n✅ 已保存 v9: {v9_path}")

    # Print remaining untranslated for review
    if untranslated > 0:
        print(f"\n剩余未翻译术语:")
        for t in terms:
            if not re.search(r'[一-鿿]', t.get("zh", "")):
                print(f"  {t['en'][:50]:50s} src: {t.get('source', '')[:20]}")

    return v8


if __name__ == "__main__":
    main()
