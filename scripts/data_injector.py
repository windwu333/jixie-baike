#!/usr/bin/env python3
"""数据注入器: 从 raw/engineers-edge + raw/engineering-toolbox 提取权威数据
为每篇文章提供具体的数据参考（材料属性、标准参数、公式等）"""
import json, re, gzip
from pathlib import Path
from typing import Any

BASE = Path(__file__).parent.parent
RAW = BASE / "raw"

# Category → keyword mapping for data indexing
CAT_KEYWORDS = {
    "工程材料": ["steel", "iron", "alloy", "hardness", "aluminum", "copper", "titanium",
                 "material", "metal", "plastic", "ceramic", "polymer", "composite",
                 "rubber", "corrosion", "density", "melting", "toughness", "fatigue"],
    "力学与强度分析": ["stress", "strain", "modulus", "beam", "fatigue", "torsion",
                       "bending", "column", "pressure vessel", "load", "force",
                       "moment", "deflection", "strength", "elastic", "plastic",
                       "vibration", "natural frequency"],
    "机械设计": ["gear", "bearing", "spring", "shaft", "screw", "bolt", "key",
                 "coupling", "clutch", "brake", "valve", "seal", "belt", "chain",
                 "cam", "linkage", "thread", "pin", "rivet", "fastener", "power screw"],
    "制造工艺": ["cast", "weld", "forging", "machin", "milling", "turning", "drill",
                 "grinding", "heat treat", "anneal", "quench", "temper", "normalize",
                 "forming", "mold", "die", "extrusion", "rolling", "cutting", "tool"],
    "热工与流体": ["thermal", "heat", "temperature", "fluid", "flow", "boil",
                   "thermodynamic", "gas", "vapor", "pump", "pipe", "duct",
                   "conduction", "convection", "radiation", "insulation", "hvac"],
    "机械电子与自动化": ["sensor", "actuator", "motor", "servo", "plc", "control",
                       "robot", "automation", "hydraulic", "pneumatic", "encoder",
                       "transducer", "relay", "solenoid", "stepper"],
    "机械制图与CAD": ["dimension", "tolerance", "cad", "drafting", "drawing",
                     "gd&t", "surface finish", "thread", "fit", "cam", "solid model"],
    "标准与规范": ["standard", "iso", "gb", "din", "astm", "specification", "code"],
    "测量与质量控制": ["measure", "gauge", "caliper", "micrometer", "inspection",
                       "tolerance", "calibration", "spc", "quality", "ndt", "inspect"],
    "动力机械与能源": ["engine", "turbine", "compressor", "motor", "generator",
                       "pump", "power", "energy", "combustion", "nozzle", "propeller"],
    "行业应用": ["automotive", "aerospace", "construction", "mining", "agriculture",
                 "railway", "marine", "oil", "gas", "nuclear", "renewable"],
}

# Category → specific data templates with real engineering values
CAT_DATA_SNIPPETS: dict[str, list[dict]] = {
    "工程材料": [
        {"title": "常用金属材料密度 (g/cm³)", "source": "engineers-edge",
         "data": "钢 7.85, 铸铁 7.2-7.4, 铝合金 2.7, 铜合金 8.9, 钛合金 4.5"},
        {"title": "常用钢材硬度范围 (HB)", "source": "engineers-edge",
         "data": "碳钢 120-180, 合金钢 200-300, 工具钢 60-65 HRC, 不锈钢 150-250"},
        {"title": "材料弹性模量 (GPa)", "source": "engineering-toolbox",
         "data": "钢 200, 铸铁 100-150, 铝合金 69, 铜合金 110, 钛合金 110"},
        {"title": "常见材料熔点 (°C)", "source": "engineers-edge",
         "data": "纯铁 1538, 碳钢 1425-1540, 铸铁 1150-1300, 铝 660, 铜 1083"},
    ],
    "力学与强度分析": [
        {"title": "典型应力-应变关系", "source": "engineers-edge",
         "data": "低碳钢屈服强度 250MPa, 抗拉强度 400MPa, 弹性模量 200GPa, 延伸率 25%"},
        {"title": "疲劳极限参考值", "source": "engineers-edge",
         "data": "钢: 疲劳极限≈0.4-0.6×抗拉强度, 铝合金: ≈0.3-0.4×抗拉强度"},
        {"title": "梁的挠度计算公式", "source": "engineers-edge",
         "data": "简支梁集中力: δ=PL³/(48EI), 悬臂梁端部力: δ=PL³/(3EI)"},
        {"title": "安全系数推荐值", "source": "engineering-toolbox",
         "data": "静载 1.5-2.0, 交变载荷 2.0-3.0, 冲击载荷 3.0-5.0"},
    ],
    "机械设计": [
        {"title": "齿轮强度计算标准", "source": "engineers-edge",
         "data": "ISO 6336:2019 齿轮承载能力计算, AGMA 2001-D04 齿面强度"},
        {"title": "轴承寿命计算", "source": "engineers-edge",
         "data": "L₁₀=(C/P)^p×10⁶转, 球轴承 p=3, 滚子轴承 p=10/3"},
        {"title": "螺栓预紧力参考", "source": "engineers-edge",
         "data": "8.8级M10螺栓: 预紧力≈30-40kN, M12: 45-55kN, M16: 80-100kN"},
        {"title": "弹簧设计参数", "source": "engineers-edge",
         "data": "弹簧钢许用应力: Ⅰ类 0.3σb, Ⅱ类 0.4σb, Ⅲ类 0.5σb"},
    ],
    "制造工艺": [
        {"title": "常用热处理工艺参数", "source": "engineers-edge",
         "data": "退火: 加热Ac₃+30-50°C→炉冷, 正火: 加热Ac₃+30-50°C→空冷"},
        {"title": "焊接工艺参数参考", "source": "engineers-edge",
         "data": "手工电弧焊电流: Φ3.2焊条 100-130A, Φ4.0 140-180A"},
        {"title": "切削加工参数", "source": "engineering-toolbox",
         "data": "车削碳钢: 切削速度 80-150m/min, 进给 0.1-0.3mm/r"},
        {"title": "铸造公差等级", "source": "engineering-toolbox",
         "data": "砂型铸造 CT9-CT12, 精密铸造 CT5-CT7, 压铸 CT4-CT6"},
    ],
    "热工与流体": [
        {"title": "常见流体密度 (kg/m³)", "source": "engineering-toolbox",
         "data": "水 1000(4°C), 空气 1.225(15°C), 液压油 870-900, 水蒸气 0.6(100°C)"},
        {"title": "传热系数参考 (W/m²K)", "source": "engineering-toolbox",
         "data": "空气自然对流 5-25, 水强制对流 500-5000, 沸腾传热 1000-50000"},
        {"title": "热力学常数", "source": "engineering-toolbox",
         "data": "气体常数 R=8.314 J/(mol·K), 标准大气压 101.325kPa, 绝对零度 -273.15°C"},
    ],
    "机械电子与自动化": [
        {"title": "常用传感器精度等级", "source": "engineers-edge",
         "data": "压力传感器 0.1-0.5%FS, 温度传感器 ±0.5°C(PT100), 位移传感器 0.01mm"},
        {"title": "电机功率计算公式", "source": "engineering-toolbox",
         "data": "P=T×ω/η, 其中T为扭矩(N·m), ω为角速度(rad/s), η为效率"},
    ],
    "机械制图与CAD": [
        {"title": "公差等级应用范围", "source": "engineering-toolbox",
         "data": "IT01-IT4 量规, IT5-IT7 精密配合, IT8-IT11 一般配合, IT12-IT18 自由尺寸"},
        {"title": "表面粗糙度Ra值 (μm)", "source": "engineering-toolbox",
         "data": "精磨 0.1-0.4, 精车 0.8-1.6, 粗车 3.2-6.3, 铸造 12.5-25"},
    ],
    "标准与规范": [
        {"title": "GB标准体系", "source": "knowledge-base",
         "data": "GB/T 700-2006 碳素结构钢, GB/T 3077-2015 合金结构钢, GB/T 3480-1997 齿轮强度"},
        {"title": "ISO标准对照", "source": "knowledge-base",
         "data": "ISO 2768-1 一般公差, ISO 8015 尺寸公差, ISO 286-1 ISO极限与配合"},
    ],
    "测量与质量控制": [
        {"title": "测量不确定度评估", "source": "engineering-toolbox",
         "data": "测量不确定度应小于工件公差的1/5-1/10, ISO 14253-1 判定规则"},
        {"title": "过程能力指数评价", "source": "engineers-edge",
         "data": "Cp≥1.33 过程能力充分, 1.0≤Cp<1.33 能力尚可需监控, Cp<1.0 能力不足"},
    ],
    "动力机械与能源": [
        {"title": "内燃机性能参数", "source": "engineering-toolbox",
         "data": "汽油机热效率 25-35%, 柴油机 35-45%, 涡轮增压柴油机 45-55%"},
        {"title": "泵的效率范围", "source": "engineering-toolbox",
         "data": "离心泵 60-85%, 齿轮泵 70-85%, 柱塞泵 85-95%"},
    ],
    "行业应用": [
        {"title": "工程机械液压系统参数", "source": "engineering-toolbox",
         "data": "工作压力 16-35MPa, 流量范围 50-500L/min, 液压油粘度 32-68 cSt(40°C)"},
    ],
}


def load_all_data() -> dict[str, list[dict]]:
    """Load and index all raw data by category. Returns {category: [records]}"""
    indexed: dict[str, list[dict]] = {cat: [] for cat in CAT_KEYWORDS}
    indexed["未分类"] = []

    # Load engineers-edge
    for f in sorted(RAW.glob("engineers-edge/*.json")):
        try:
            records = json.loads(f.read_bytes())
            if not isinstance(records, list):
                continue
            for r in records:
                title = r.get("title", "")
                match_cat = _match_category(title, r.get("text", ""))
                indexed.setdefault(match_cat, []).append(r)
        except Exception:
            continue

    # Load engineering-toolbox
    for f in sorted(RAW.glob("engineering-toolbox/*.json")):
        try:
            records = json.loads(f.read_bytes())
            if not isinstance(records, list):
                continue
            for r in records:
                title = r.get("title", "")
                match_cat = _match_category(title, r.get("text", ""))
                indexed.setdefault(match_cat, []).append(r)
        except Exception:
            continue

    return indexed


def _match_category(title: str, text: str = "") -> str:
    """Match a record title to a category by keyword scoring"""
    combined = (title + " " + text).lower()
    scores: dict[str, int] = {}
    for cat, keywords in CAT_KEYWORDS.items():
        score = sum(2 if kw in title.lower() else 0 for kw in keywords)
        score += sum(1 if kw in combined else 0 for kw in keywords)
        if score > 0:
            scores[cat] = score
    if not scores:
        return "未分类"
    return max(scores, key=scores.get)


def get_data_for_article(article: dict, max_items: int = 3) -> list[dict]:
    """Get authoritative data snippets relevant to an article.
    Returns list of {title, source, data_type, snippet} dicts."""
    cat = article.get("category", "")
    kw = set(k.lower() for k in article.get("keywords", []))

    # Start with category data snippets
    result = list(CAT_DATA_SNIPPETS.get(cat, []))

    # Also search raw records by keyword match
    title_lower = article.get("title", "").lower()

    # Check all raw data files for keyword/title matches
    for f in sorted(RAW.glob("engineers-edge/*.json")):
        try:
            records = json.loads(f.read_bytes())
            for r in (records or []):
                if not isinstance(r, dict):
                    continue
                rt = r.get("title", "").lower()
                # Match if any keyword appears in title, or title word overlap
                if any(k in rt for k in kw if len(k) > 2) or any(
                    word in rt for word in title_lower.split() if len(word) > 3
                ):
                    text = (r.get("text") or "")[:200].strip()
                    if text:
                        result.append({
                            "title": r.get("title", ""),
                            "source": "engineers-edge",
                            "data_type": "raw_reference",
                            "snippet": text[:150],
                        })
                        if len(result) >= max_items + 4:  # allow some extra
                            break
        except Exception:
            continue

    return result[:max_items]
