#!/usr/bin/env python3
"""参考来源富集: 从所有raw sources构建完整引用数据库
输出 knowledge-base/reference-database.json — 含URL/平台/标题/作者/类别
用于 generate-content-v2.py 注入维基风格引用"""

import json, re
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.parent
RAW = BASE / "raw"
KB = BASE / "knowledge-base"

# 平台元数据
PLATFORM_META = {
    "engineers-edge": {
        "name": "Engineers Edge",
        "url": "https://www.engineersedge.com",
        "description": "工程资源与计算器参考平台",
        "type": "engineering_reference",
        "attribution": "Engineers Edge",
    },
    "engineering-toolbox": {
        "name": "Engineering ToolBox",
        "url": "https://www.engineeringtoolbox.com",
        "description": "工程工具与基础信息参考",
        "type": "engineering_reference",
        "attribution": "Engineering ToolBox",
    },
    "efunda": {
        "name": "eFunda",
        "url": "https://www.efunda.com",
        "description": "在线工程参考大全",
        "type": "engineering_reference",
        "attribution": "eFunda, Inc.",
    },
    "explainthatstuff": {
        "name": "Explain that Stuff",
        "url": "https://www.explainthatstuff.com",
        "description": "科普与技术解释网站",
        "type": "science_education",
        "attribution": "Chris Woodford / Explain that Stuff",
    },
    "nasa-ntrs": {
        "name": "NASA Technical Reports Server (NTRS)",
        "url": "https://ntrs.nasa.gov",
        "description": "NASA技术报告数据库",
        "type": "government_research",
        "attribution": "NASA STI Program",
    },
    "nist-engineering": {
        "name": "NIST Engineering",
        "url": "https://www.nist.gov/engineering",
        "description": "美国国家标准与技术研究院工程部",
        "type": "government_standard",
        "attribution": "National Institute of Standards and Technology",
    },
    "arxiv-me": {
        "name": "arXiv Mechanical Engineering",
        "url": "https://arxiv.org",
        "description": "预印本论文存档(机械工程相关)",
        "type": "academic_preprint",
        "attribution": "arXiv.org / Cornell University",
    },
    "britannica-engineering": {
        "name": "Encyclopædia Britannica (Engineering)",
        "url": "https://www.britannica.com/engineering",
        "description": "大英百科全书工程学条目",
        "type": "encyclopedia",
        "attribution": "Encyclopædia Britannica, Inc.",
    },
    "howstuffworks-eng": {
        "name": "HowStuffWorks (Engineering)",
        "url": "https://www.howstuffworks.com/engineering",
        "description": "工程科普网站",
        "type": "science_education",
        "attribution": "HowStuffWorks / InfoSpace Holdings",
    },
}

# 类别关键词映射(与data_injector.py同步)
CAT_KEYWORDS = {
    "工程材料": ["material", "steel", "iron", "alloy", "hardness", "aluminum", "copper",
                 "metal", "plastic", "ceramic", "polymer", "composite", "corrosion",
                 "density", "melting", "toughness", "fatigue", "heat treat"],
    "力学与强度分析": ["stress", "strain", "modulus", "beam", "fatigue", "torsion",
                       "bending", "column", "pressure vessel", "load", "force",
                       "moment", "deflection", "strength", "elastic", "plastic",
                       "vibration", "natural frequency", "mechanics"],
    "机械设计": ["gear", "bearing", "spring", "shaft", "screw", "bolt", "key",
                 "coupling", "clutch", "brake", "valve", "seal", "belt", "chain",
                 "cam", "linkage", "thread", "pin", "rivet", "fastener", "power screw",
                 "design", "joint"],
    "制造工艺": ["cast", "weld", "forging", "machin", "milling", "turning", "drill",
                 "grinding", "heat treat", "anneal", "quench", "temper", "normalize",
                 "forming", "mold", "die", "extrusion", "rolling", "cutting", "tool",
                 "manufacturing", "fabrication", "assembly"],
    "热工与流体": ["thermal", "heat", "temperature", "fluid", "flow", "boil",
                   "thermodynamic", "gas", "vapor", "pump", "pipe", "duct",
                   "conduction", "convection", "radiation", "insulation", "hvac",
                   "hydraulic", "pneumatic"],
    "机械电子与自动化": ["sensor", "actuator", "motor", "servo", "plc", "control",
                       "robot", "automation", "hydraulic", "pneumatic", "encoder",
                       "transducer", "relay", "solenoid", "stepper", "electronics"],
    "机械制图与CAD": ["dimension", "tolerance", "cad", "drafting", "drawing",
                     "gd&t", "surface finish", "thread", "fit", "cam", "solid model",
                     "sketch", "modeling", "autocad", "solidworks"],
    "标准与规范": ["standard", "iso", "gb", "din", "astm", "specification", "code",
                   "regulation", "compliance"],
    "测量与质量控制": ["measure", "gauge", "caliper", "micrometer", "inspection",
                       "tolerance", "calibration", "spc", "quality", "ndt",
                       "inspect", "metrology"],
    "动力机械与能源": ["engine", "turbine", "compressor", "motor", "generator",
                       "pump", "power", "energy", "combustion", "nozzle", "propeller",
                       "internal combustion"],
    "行业应用": ["automotive", "aerospace", "construction", "mining", "agriculture",
                 "railway", "marine", "oil", "gas", "nuclear", "renewable",
                 "industry", "application"],
}


def _match_category(title: str, text: str = "") -> str:
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


def load_index_records():
    """Load unified index"""
    f = RAW / ".index.json"
    if not f.exists():
        return []
    data = json.loads(f.read_text())
    return data.get("records", [])


def load_raw_data(source_id: str) -> list[dict]:
    """Load raw JSON records for a given source_id directory"""
    src_dir = RAW / source_id
    if not src_dir.exists():
        return []
    records = []
    for f in sorted(src_dir.glob("*.json")):
        try:
            data = json.loads(f.read_bytes())
            if isinstance(data, list):
                records.extend(data)
            elif isinstance(data, dict):
                records.append(data)
        except Exception:
            continue
    return records


def build_reference(ref_id: str, url: str, title: str, source_id: str,
                    platform_meta: dict, category: str = "") -> dict:
    """Build a unified reference entry"""
    return {
        "id": ref_id,
        "url": url,
        "title": title,
        "source_id": source_id,
        "platform_name": platform_meta.get("name", source_id),
        "platform_url": platform_meta.get("url", ""),
        "attribution": platform_meta.get("attribution", ""),
        "source_type": platform_meta.get("type", "unknown"),
        "category": category,
        "cite_text": f"{platform_meta.get('name', source_id)}, 「{title}」",
    }


def build_database() -> dict:
    """Build unified reference database from all sources"""
    index_records = load_index_records()
    index_by_url: dict[str, dict] = {}
    for r in index_records:
        url = r.get("url", "")
        if url:
            index_by_url[url] = r

    references: list[dict] = []
    seen_urls: set[str] = set()
    ref_id = 0

    # Process each source directory
    for source_id in ["engineers-edge", "engineering-toolbox", "efunda",
                       "explainthatstuff", "nasa-ntrs", "nist-engineering",
                       "arxiv-me"]:
        raw_records = load_raw_data(source_id)
        platform_meta = PLATFORM_META.get(source_id, {})
        if not platform_meta:
            continue

        for r in raw_records:
            url = r.get("url", "") or ""
            title = r.get("title", "") or r.get("name", "") or ""
            # Fix relative URLs
            if url and url.startswith("/"):
                url = platform_meta.get("url", "") + url
            if not url or not title:
                continue
            if url in seen_urls:
                continue
            seen_urls.add(url)

            # Determine category from title+content
            content = (r.get("content", "") or r.get("text", "") or "")[:500]
            category = _match_category(title, content)

            ref_id += 1
            ref = build_reference(f"ref-{ref_id:04d}", url, title,
                                  source_id, platform_meta, category)

            # Add extra fields from index if available
            index_rec = index_by_url.get(url, {})
            if index_rec:
                ref["quality_score"] = index_rec.get("quality_score", 0)
                ref["source_tier"] = index_rec.get("source_tier", "")

            references.append(ref)

    # Sort by category then quality
    references.sort(key=lambda r: (r.get("category", ""),
                                   0 if r.get("source_tier") == "A" else
                                   1 if r.get("source_tier") == "B" else 2))

    return {
        "meta": {
            "total": len(references),
            "sources": list(PLATFORM_META.keys()),
            "version": "1.0",
            "generated": "2026-05-18",
        },
        "platforms": {k: {kk: vv for kk, vv in v.items() if kk != "url"}
                      for k, v in PLATFORM_META.items()},
        "references": references,
    }


def get_references_for_keyword(keyword: str, db: dict, max_items: int = 5) -> list[dict]:
    """Get references relevant to a keyword"""
    kw_lower = keyword.lower()
    matched = []
    for ref in db["references"]:
        title = ref.get("title", "").lower()
        if kw_lower in title:
            matched.append(ref)
        if len(matched) >= max_items:
            break
    return matched


def get_references_for_category(category: str, db: dict, max_items: int = 8) -> list[dict]:
    """Get top references for a category"""
    matched = []
    for ref in db["references"]:
        if ref.get("category") == category:
            matched.append(ref)
        if len(matched) >= max_items + 5:
            break
    return matched[:max_items]


if __name__ == "__main__":
    db = build_database()
    out_path = KB / "reference-database.json"
    out_path.write_text(json.dumps(db, ensure_ascii=False, indent=2))
    total = db["meta"]["total"]

    # Stats by category
    from collections import Counter
    cat_counts = Counter(r.get("category", "未分类") for r in db["references"])
    print(f"Reference database built: {total} entries -> {out_path}")
    print("\nBy category:")
    for c, n in cat_counts.most_common():
        print(f"  {c}: {n}")
    print("\nBy source:")
    src_counts = Counter(r.get("source_id") for r in db["references"])
    for s, n in src_counts.most_common():
        print(f"  {s}: {n}")
