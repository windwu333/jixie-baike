#!/usr/bin/env python3
"""从 Wikipedia 词条数据提取中英机械工程术语对照表"""
import json, re, sys
from pathlib import Path

WIKI_FILE = Path(__file__).parent.parent / "knowledge-base" / "wikipedia-pages.json"
OUTPUT_JSON = Path(__file__).parent.parent / "knowledge-base" / "mech-terminology.json"
OUTPUT_MD = Path(__file__).parent.parent / "knowledge-base" / "mech-terminology.md"

# 已知机械工程术语中英对照种子库（核心术语）
SEED_TERMS = {
    # 材料
    "steel": "钢", "cast iron": "铸铁", "stainless steel": "不锈钢", "alloy": "合金",
    "aluminum": "铝", "copper": "铜", "titanium": "钛", "nickel": "镍",
    "heat treatment": "热处理", "annealing": "退火", "quenching": "淬火",
    "tempering": "回火", "carburizing": "渗碳", "nitriding": "渗氮",
    "hardness": "硬度", "toughness": "韧性", "fatigue": "疲劳", "creep": "蠕变",
    "yield strength": "屈服强度", "tensile strength": "抗拉强度",
    "corrosion": "腐蚀", "wear": "磨损",
    # 力学
    "stress": "应力", "strain": "应变", "bending": "弯曲", "torsion": "扭转",
    "vibration": "振动", "modal analysis": "模态分析", "finite element": "有限元",
    "fatigue life": "疲劳寿命", "fracture": "断裂", "crack propagation": "裂纹扩展",
    "tribology": "摩擦学", "lubrication": "润滑", "bearing": "轴承",
    # 设计
    "gear": "齿轮", "worm gear": "蜗杆", "belt drive": "带传动",
    "chain drive": "链传动", "shaft": "轴", "coupling": "联轴器",
    "clutch": "离合器", "brake": "制动器", "spring": "弹簧",
    "seal": "密封", "fastener": "紧固件", "bolt": "螺栓", "nut": "螺母",
    "screw": "螺钉", "key": "键", "pin": "销", "weld": "焊接",
    "tolerance": "公差", "fit": "配合", "clearance": "间隙",
    # 制造
    "casting": "铸造", "forging": "锻造", "machining": "机械加工",
    "turning": "车削", "milling": "铣削", "drilling": "钻孔", "grinding": "磨削",
    "CNC": "数控", "additive manufacturing": "增材制造", "3D printing": "3D打印",
    "stamping": "冲压", "extrusion": "挤压", "rolling": "轧制",
    "surface treatment": "表面处理", "coating": "涂层", "plating": "电镀",
    "injection molding": "注塑成型",
    # 热工流体
    "thermodynamics": "热力学", "heat transfer": "传热学",
    "fluid mechanics": "流体力学", "hydraulics": "液压", "pneumatics": "气动",
    "pump": "泵", "valve": "阀门", "compressor": "压缩机",
    "heat exchanger": "换热器", "boiler": "锅炉", "turbine": "涡轮机",
    "internal combustion engine": "内燃机",
    # 机电
    "sensor": "传感器", "actuator": "执行器", "servo motor": "伺服电机",
    "stepper motor": "步进电机", "PLC": "可编程逻辑控制器",
    "robot": "机器人", "automation": "自动化", "mechatronics": "机电一体化",
    # 制图
    "CAD": "计算机辅助设计", "CAM": "计算机辅助制造",
    "dimension": "尺寸", "tolerance": "公差", "GD&T": "几何尺寸与公差",
    "assembly": "装配", "exploded view": "爆炸图",
    # 标准
    "ISO": "国际标准化组织", "ASTM": "美国材料与试验协会",
    "DIN": "德国标准", "quality control": "质量控制",
    "inspection": "检验", "calibration": "校准",
}

def extract_terms_from_text(text):
    """Extract potential technical terms from English text."""
    # Find capitalized multi-word phrases that are likely technical terms
    phrases = re.findall(r'\b([A-Z][a-z]+(?:\s+[a-z]+)*)\b', text)
    # Single technical words
    single_words = re.findall(r'\b([a-z]{4,})\b', text.lower())
    return phrases, single_words

def main():
    # Load Wikipedia data
    data = json.loads(WIKI_FILE.read_text())
    pages = data.get("all_pages", [])

    # Start with seed terms
    terminology = {}
    for eng, chn in SEED_TERMS.items():
        terminology[eng.lower()] = {
            "en": eng,
            "zh": chn,
            "source": "seed",
            "category": "core",
        }

    # Extract unique terms from page titles
    for page in pages:
        title = page["title"]
        extract = page.get("extract", "")
        # Add page title as a potential term
        if title.lower() not in terminology:
            terminology[title.lower()] = {
                "en": title,
                "zh": "",  # To be filled
                "source": "wikipedia_title",
                "category": "auto_extracted",
            }

    # Categorize
    for key, entry in terminology.items():
        if entry["source"] == "seed":
            continue
        # Try to auto-categorize based on keywords
        title_lower = entry["en"].lower()
        if any(kw in title_lower for kw in ["gear", "bearing", "shaft", "spring", "bolt", "screw",
                                              "fastener", "clutch", "brake", "coupling", "valve",
                                              "pump", "seal", "belt", "chain", "key", "pin"]):
            entry["category"] = "机械设计"
        elif any(kw in title_lower for kw in ["steel", "alloy", "metal", "polymer", "ceramic",
                                               "composite", "corrosion", "heat treatment",
                                               "hardness", "fatigue", "fracture"]):
            entry["category"] = "工程材料"
        elif any(kw in title_lower for kw in ["cast", "forge", "weld", "machin", "mill", "turn",
                                               "drill", "grind", "CNC", "stamp", "extrusion",
                                               "additive", "mold", "surface"]):
            entry["category"] = "制造工艺"
        elif any(kw in title_lower for kw in ["thermo", "fluid", "hydraulic", "pneumatic",
                                               "heat transfer", "pump", "compressor", "turbine"]):
            entry["category"] = "热工流体"
        elif any(kw in title_lower for kw in ["sensor", "actuator", "servo", "robot",
                                               "automation", "control", "motor", "PLC"]):
            entry["category"] = "机电自动化"
        elif any(kw in title_lower for kw in ["stress", "strain", "vibration", "finite element",
                                               "modal", "tribology", "lubrication", "dynamics"]):
            entry["category"] = "力学强度"
        elif any(kw in title_lower for kw in ["CAD", "drafting", "dimension", "tolerance",
                                               "GD&T", "drawing"]):
            entry["category"] = "制图CAD"
        elif any(kw in title_lower for kw in ["ISO", "standard", "quality", "inspection",
                                               "calibration", "ASTM", "DIN"]):
            entry["category"] = "标准规范"
        else:
            entry["category"] = "未分类"

    # Sort - seed terms first, then by category, then alphabetically
    seed_list = [v for v in terminology.values() if v["source"] == "seed"]
    extracted_list = [v for v in terminology.values() if v["source"] != "seed"]

    # Output seed terms with filled categories
    output = {
        "meta": {
            "title": "机械工程中英术语对照表",
            "version": "1.0",
            "created": "2026-05-18",
            "total_terms": len(terminology),
            "seed_terms": len(seed_list),
            "extracted_terms": len(extracted_list),
        },
        "terms": sorted(seed_list, key=lambda t: t["en"]),
        "extracted_extras": sorted(extracted_list, key=lambda t: t["category"])[:200],
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2))

    # Also generate Markdown
    categories = {}
    for t in seed_list:
        cat = t["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(t)

    md_lines = [
        "# 机械工程中英术语对照表\n",
        f"> 版本 1.0 | 2026-05-18 | 总计 {len(seed_list)} 条核心术语 + {len(extracted_list)} 条自动提取\n",
        "---\n",
    ]

    cat_order = ["core", "工程材料", "力学强度", "机械设计", "制造工艺", "热工流体",
                 "机电自动化", "制图CAD", "标准规范", "未分类"]
    for cat in cat_order:
        if cat not in categories:
            continue
        md_lines.append(f"\n## {cat}\n")
        md_lines.append("| 英文 | 中文 |\n|------|------|\n")
        for t in sorted(categories[cat], key=lambda x: x["en"]):
            md_lines.append(f"| {t['en']} | {t['zh']} |\n")

    md_lines.append(f"\n---\n## 自动提取词条（前200条）\n")
    md_lines.append("| 英文 | 推测分类 |\n|------|---------|\n")
    for t in extracted_list[:200]:
        md_lines.append(f"| {t['en']} | {t['category']} |\n")

    OUTPUT_MD.write_text("".join(md_lines))
    print(f"✅ 术语表: {len(seed_list)} 核心 + {len(extracted_list)} 自动提取", file=sys.stderr)
    print(f"   JSON: {OUTPUT_JSON}", file=sys.stderr)
    print(f"   MD:   {OUTPUT_MD}", file=sys.stderr)

if __name__ == "__main__":
    main()
